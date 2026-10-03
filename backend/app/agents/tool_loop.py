from langchain_core.messages import HumanMessage, ToolMessage

from app.agents.llm import llm_with_tools
from app.tools.logs import search_logs


TOOLS = {
    "search_logs": search_logs,
}


def investigate_with_tools(incident: str) -> str:
    messages = [HumanMessage(content=incident)]

    response = llm_with_tools.invoke(messages)
    messages.append(response)

    while response.tool_calls:
        for tool_call in response.tool_calls:
            tool = TOOLS[tool_call["name"]]

            result = tool.invoke(tool_call["args"])

            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"],
                )
            )

        response = llm_with_tools.invoke(messages)
        messages.append(response)

    if isinstance(response.content, list):
        return "\n".join(
            item["text"]
            for item in response.content
            if isinstance(item, dict) and item.get("type") == "text"
        )

    return str(response.content)