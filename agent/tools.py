"""Tool registry and execution: everything the Planner can call besides the LLM roles."""
from db.supabase_client import get_recent_user_transactions, get_transaction, get_user_summary
from rag.retriever import search_fraud_knowledge

TOOLS = {
    "get_transaction": get_transaction,
    "get_user_summary": get_user_summary,
    "get_recent_user_transactions": get_recent_user_transactions,
    "search_fraud_knowledge": search_fraud_knowledge,
}


def execute_tool(tool_name: str, arguments: dict) -> dict:
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        return TOOLS[tool_name](**arguments)
    except Exception as e:
        return {"error": str(e)}


def run_selected_tool(action: str, arguments: dict):
    if action == "assess":
        return None
    return execute_tool(action, arguments)


def update_state_from_tool(state: dict, action: str, result) -> dict:
    if action == "get_transaction":
        state["target_transaction"] = result
    elif action == "get_user_summary":
        state["user_summary"] = result
    elif action == "get_recent_user_transactions":
        state["recent_transactions"] = result
    elif action == "search_fraud_knowledge":
        state["knowledge_results"].append(result)

    if action in state["tool_status"]:
        if result is None or result == []:
            state["tool_status"][action] = "called_no_result"
        else:
            state["tool_status"][action] = "called_with_result"

    return state
