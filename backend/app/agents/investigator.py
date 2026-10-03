from app.agents.llm import llm


INVESTIGATOR_PROMPT = """
You are OpsPilot, an AI production incident investigator.

Your job is to analyze a production incident and determine:
1. What is happening?
2. What is the most likely root cause?
3. What evidence supports that conclusion?
4. What should an engineer investigate or do next?

Be precise.
Do not invent evidence.
If the available information is insufficient, explicitly say so.

Incident:
{incident}
"""


def investigate_incident(incident: str) -> str:
    prompt = INVESTIGATOR_PROMPT.format(incident=incident)

    response = llm.invoke(prompt)

    if isinstance(response.content, list):
        return "\n".join(
            item["text"]
            for item in response.content
            if isinstance(item, dict) and item.get("type") == "text"
        )

    return str(response.content)