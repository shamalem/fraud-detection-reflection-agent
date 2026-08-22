"""Agent state: what the Planner sees, and the registry of actions it can choose from."""

AGENT_ACTIONS = {
    "get_transaction": {
        "description": "Retrieve one transaction by Transaction_ID.",
        "arguments": ["transaction_id"],
    },
    "get_user_summary": {
        "description": "Retrieve a compact summary of the user's historical behavior before the target transaction timestamp.",
        "arguments": ["user_id", "before_timestamp"],
    },
    "get_recent_user_transactions": {
        "description": "Retrieve recent transactions for a user that occurred before the target transaction timestamp.",
        "arguments": ["user_id", "before_timestamp", "limit"],
    },
    "search_fraud_knowledge": {
        "description": "Search the Mastercard and ECB fraud knowledge base. The agent must create the search query itself.",
        "arguments": ["query"],
    },
    "assess": {
        "description": "Move to the RiskAssessor when sufficient evidence has been collected.",
        "arguments": [],
    },
}

AGENT_DECISION_SCHEMA = {
    "action": "one of the available actions",
    "arguments": {},
    "reason": "why this is the best next action",
}


def create_agent_state(transaction_id: str) -> dict:
    return {
        "transaction_id": transaction_id,
        "target_transaction": None,
        "user_summary": None,
        "recent_transactions": None,
        "knowledge_results": [],
        "draft_assessment": None,
        "reflection": None,
        "final_answer": None,
        "iteration": 0,
        "tool_status": {
            "get_transaction": "not_called",
            "get_user_summary": "not_called",
            "get_recent_user_transactions": "not_called",
            "search_fraud_knowledge": "not_called",
        },
    }
