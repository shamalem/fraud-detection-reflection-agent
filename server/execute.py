"""Logic for POST /api/execute - the agent's main entry point.

Input:  {"prompt": "..."}
Output: {"status", "error", "response", "steps"} - exactly the shape run_agent()
        already returns; this module just extracts a transaction id from the
        free-text prompt and calls it.
"""
import re

TRANSACTION_ID_PATTERN = re.compile(r"TXN_[0-9]+", re.IGNORECASE)


def _error(message: str) -> dict:
    return {"status": "error", "error": message, "response": None, "steps": []}


def handle_prompt(prompt) -> dict:
    if not prompt or not str(prompt).strip():
        return _error("The 'prompt' field is required and cannot be empty.")

    match = TRANSACTION_ID_PATTERN.search(str(prompt))
    if not match:
        return _error(
            "Could not find a transaction ID in the prompt. Include one in the "
            "form TXN_<id>, e.g. 'Investigate transaction TXN_10002'."
        )

    from agent.orchestrator import run_agent

    return run_agent(match.group(0).upper())
