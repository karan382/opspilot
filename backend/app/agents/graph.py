import time

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.agents.llm import llm, structured_llm
from app.models.investigation import InvestigationReport
from app.tools.deployments import search_deployments
from app.tools.knowledge import search_knowledge
from app.tools.logs import search_logs
from app.tools.metrics import query_metrics


TOOLS = [
    search_logs,
    search_knowledge,
    search_deployments,
    query_metrics,
]

llm_with_tools = llm.bind_tools(TOOLS)


class InvestigationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    report: InvestigationReport | None
    iterations: int
    incident_id: str


def investigator(state: InvestigationState):
    investigation_guidance = HumanMessage(
        content="""
Investigation rules:
- Identify the affected service from the incident before using tools.
- For logs, metrics, and deployments, always use the exact affected service.
- Do not query unrelated services just because relevant-looking data exists.
- If a service-specific tool returns no results, treat that as an evidence gap.
- For knowledge searches, include the affected service and observed symptoms
  when relevant.
- Prefer collecting evidence from the affected service before drawing conclusions.
"""
    )

    response = llm_with_tools.invoke(
        state["messages"] + [investigation_guidance]
    )

    return {
        "messages": [response],
        "iterations": state["iterations"] + 1,
    }


def generate_report(state: InvestigationState):
    evidence_parts = []

    for message in state["messages"]:
        if getattr(message, "type", None) == "tool":
            tool_name = getattr(message, "name", "unknown_tool")
            evidence_parts.append(
                f"SOURCE: {tool_name}\n{message.content}"
            )

    evidence = "\n\n".join(evidence_parts)
    
    if not evidence.strip():
        return {
            "report": InvestigationReport(
                summary="Insufficient evidence was collected to investigate the incident.",
                timeline=[],
                evidence=[],
                root_cause={
                    "hypothesis": "Unable to determine root cause from the available evidence.",
                    "confidence": 0.0,
                    "reasoning": "No tool returned usable investigation evidence.",
                    "claim_level": "unconfirmed",
                },
                recommendations=[
                    "Collect relevant logs, metrics, deployment history, and runbook information before drawing a root-cause conclusion."
                ],
                uncertainties=["No investigation evidence was available."],
            )
        }

    incident = next(
        (
            message.content
            for message in state["messages"]
            if getattr(message, "type", None) == "human"
        ),
        "",
    )

    prompt = f"""
    You are OpsPilot, an AI production incident investigator.

    Investigate the incident described below and create a final incident
    investigation report using ONLY the incident description and collected
    evidence.

    Original incident:
    {incident}

    Collected evidence:
    {evidence}

STRICT RULES:
- Do not invent evidence.
- Do not invent timestamps.
- Do not invent deployments.
- Do not invent metrics.
- Do not invent logs.
- Do not invent external systems or sources.
- Distinguish confirmed evidence from hypotheses.
- Do not describe an observed symptom as the cause of another symptom unless the collected evidence establishes that causal relationship.
- When evidence only shows correlated symptoms, describe them as observations and keep the causal trigger unconfirmed.
- If the evidence is insufficient to establish something, put it in uncertainties.
- Confidence must reflect the evidence actually available.
- Prefer the strongest explanation supported by multiple independent pieces of evidence.
- When deployment timing, logs, metrics, and recovery behavior consistently support a root cause, treat that correlation as meaningful evidence.
- Do not claim that profiling, tracing, or other evidence is required when the provided evidence is already sufficient to establish a likely root cause.
- Clearly distinguish "confirmed by evidence" from "likely root cause" and "unconfirmed hypothesis".
- Set root_cause.claim_level to one of: "confirmed", "strongly_supported", "likely", or "unconfirmed".
- Use "confirmed" only when the collected evidence directly establishes the claim.
- Use "strongly_supported" when multiple independent signals strongly support the claim but do not directly prove the exact causal mechanism.
- Use "likely" when the evidence supports a plausible explanation but important alternatives or missing evidence remain.
- Use "unconfirmed" when the evidence is insufficient to support the hypothesis.
- "description" should explain why the evidence is relevant to the investigation.
- "observation" should contain only the concrete factual observation extracted from the source, including exact values or wording when available.
- For every evidence item, provide a concise observation containing the exact factual signal from the source (for example, metric values, log message, deployment change, or document statement).
- Do not describe an event as "immediate", "instant", "direct", or "immediately following" unless the collected evidence explicitly supports that temporal relationship. Use the actual observed timestamps instead.
- Do not attribute causality to one specific change when the evidence only establishes that multiple changes occurred together. State the supported relationship and identify the unresolved causal mechanism as an uncertainty.
"""

    for attempt in range(3):
        try:
            report = structured_llm.invoke(prompt)
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    report = report.model_copy(update={"incident_id": state["incident_id"]})

    return {"report": report}


MAX_ITERATIONS = 5


def should_continue(state: InvestigationState):
    last_message = state["messages"][-1]

    if state["iterations"] >= MAX_ITERATIONS:
        return "report"

    if last_message.tool_calls:
        return "tools"

    return "report"


tool_node = ToolNode(TOOLS)


graph_builder = StateGraph(InvestigationState)

graph_builder.add_node("investigator", investigator)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("report", generate_report)

graph_builder.add_edge(START, "investigator")

graph_builder.add_conditional_edges(
    "investigator",
    should_continue,
    {
        "tools": "tools",
        "report": "report",
    },
)

graph_builder.add_edge("tools", "investigator")
graph_builder.add_edge("report", END)

graph = graph_builder.compile()