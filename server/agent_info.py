"""Data for GET /api/agent_info: description, purpose, prompt template, worked example.

The example's system prompts are imported from agent/prompts.py (the real prompts
the deployed agent uses), so this documentation can't drift out of sync with the
actual code. The user/response content is a static, illustrative worked example -
not a live LLM call - matching the format required by the course project spec.
"""
import json

from agent.prompts import (
    PLANNER_SYSTEM_PROMPT,
    REFLECTOR_SYSTEM_PROMPT,
    RISK_ASSESSOR_SYSTEM_PROMPT,
)

DESCRIPTION = (
    "An autonomous fraud-triage agent for a single transaction alert. A Planner "
    "decides, one step at a time, which evidence to gather next (no fixed "
    "sequence) - the transaction itself, the account's history, or the Mastercard/"
    "ECB fraud-policy knowledge base. Once it has enough evidence, a RiskAssessor "
    "drafts a structured risk assessment, and a Reflector audits that draft "
    "against the same evidence before it is returned - approving it, sending it "
    "back for revision, or asking the Planner to gather more evidence first.\n\n"
    "What it CAN do: investigate one transaction at a time by its Transaction_ID, "
    "pull the account's transaction history, search fraud-policy documents for "
    "relevant guidance, and return a grounded priority, risk factors, and "
    "recommended action.\n\n"
    "What it CANNOT do (constraints): it never makes a final fraud determination "
    "- only a human analyst does; every claim in its output must be traceable to "
    "the transaction data, the account history, or retrieved policy text (it is "
    "explicitly instructed not to invent thresholds, patterns, or interpretations "
    "unsupported by evidence); and it only investigates transactions that exist "
    "in the connected database."
)

PURPOSE = (
    "Cut fraud-alert triage time for small teams by autonomously gathering "
    "evidence and drafting a grounded, explainable risk assessment - checked by "
    "a second independent pass - before a human analyst ever sees the case."
)

PROMPT_TEMPLATE = {
    "template": "Investigate transaction <TRANSACTION_ID>",
    "example": "Investigate transaction TXN_10002",
}

_EXAMPLE_TRANSACTION = {
    "Transaction_ID": "TXN_DEMO_001",
    "User_ID": "USER_DEMO",
    "Timestamp": "2024-03-14T02:10:00+00:00",
    "Transaction_Amount": 2850.00,
    "Transaction_Type": "Online",
    "Location": "Lagos",
    "Device_Type": "Mobile",
    "IP_Address_Flag": 1,
    "Previous_Fraudulent_Activity": 0,
    "Failed_Transaction_Count_7d": 3,
    "Authentication_Method": "Password",
}

_FULL_RESPONSE = {
    "risk_level": "high",
    "confidence": 0.72,
    "key_risk_factors": [
        "IP_Address_Flag = 1",
        "Location differs from historical baseline (Lagos vs Chicago)",
        "Transaction_Amount is ~15.8x the user's historical average (2850.00 vs 180.0)",
    ],
    "supporting_evidence": [
        "Retrieved Mastercard/ECB guidance: flagged IP + new location + amount "
        "step-up is consistent with account takeover",
    ],
    "recommended_action": "Hold the transaction and verify with the cardholder before processing.",
    "reasoning_summary": (
        "Flagged IP, unfamiliar location, and a ~15.8x amount step-up together "
        "match retrieved account-takeover guidance."
    ),
}


def _step(module, system_prompt, user_prompt, response):
    return {"module": module, "prompt": {"system_prompt": system_prompt, "user_prompt": user_prompt}, "response": response}


PROMPT_EXAMPLES = [
    {
        "prompt": "Investigate transaction TXN_DEMO_001",
        "full_response": _FULL_RESPONSE,
        "steps": [
            _step(
                "Planner",
                PLANNER_SYSTEM_PROMPT,
                "Current investigation state: {transaction_id: TXN_DEMO_001, target_transaction: null, ...}",
                {"action": "get_transaction", "arguments": {"transaction_id": "TXN_DEMO_001"}, "reason": "Need the target transaction first."},
            ),
            _step(
                "Planner",
                PLANNER_SYSTEM_PROMPT,
                "Current investigation state: {target_transaction: {...}, user_summary: null, ...}",
                {"action": "get_user_summary", "arguments": {"user_id": "USER_DEMO", "before_timestamp": "2024-03-14T02:10:00+00:00"}, "reason": "Need a behavioral baseline for this user."},
            ),
            _step(
                "Planner",
                PLANNER_SYSTEM_PROMPT,
                "Current investigation state: {target_transaction: {...}, user_summary: {...}, knowledge_results: [], ...}",
                {"action": "search_fraud_knowledge", "arguments": {"query": "flagged IP address, new location, elevated amount"}, "reason": "IP flag plus location/amount shift may match a known fraud pattern."},
            ),
            _step(
                "Planner",
                PLANNER_SYSTEM_PROMPT,
                "Current investigation state: {target_transaction: {...}, user_summary: {...}, knowledge_results: [{...}], ...}",
                {"action": "assess", "arguments": {}, "reason": "Sufficient evidence collected."},
            ),
            _step(
                "RiskAssessor",
                RISK_ASSESSOR_SYSTEM_PROMPT,
                f"Assess the fraud risk of the target transaction using only the collected evidence below.\n\nEvidence:\n{json.dumps({'target_transaction': _EXAMPLE_TRANSACTION}, indent=2)}",
                {
                    "risk_level": "high",
                    "confidence": 0.55,
                    "key_risk_factors": ["IP_Address_Flag = 1", "Location differs from historical baseline (Lagos vs Chicago)"],
                    "supporting_evidence": ["Transaction_Amount 2850.00 vs historical average 180.0"],
                    "recommended_action": "Block and contact cardholder.",
                    "reasoning_summary": "Amount is unusually high, so this is likely fraud.",
                },
            ),
            _step(
                "Reflector",
                REFLECTOR_SYSTEM_PROMPT,
                "Critically review the draft fraud assessment using only the evidence below. ...",
                {
                    "decision": "REVISE",
                    "issues": [
                        "'unusually high' is asserted without citing the historical baseline ratio",
                        "retrieved knowledge chunk was not cited despite matching the pattern",
                    ],
                    "reason": "Draft's conclusion is directionally right but not fully grounded in the cited evidence.",
                    "suggested_next_action": None,
                    "suggested_search_query": None,
                },
            ),
            _step(
                "RiskAssessor",
                RISK_ASSESSOR_SYSTEM_PROMPT,
                "Revise the previous fraud assessment using the reflection feedback. ...",
                _FULL_RESPONSE,
            ),
            _step(
                "Reflector",
                REFLECTOR_SYSTEM_PROMPT,
                "Critically review the draft fraud assessment using only the evidence below. ...",
                {"decision": "APPROVE", "issues": [], "reason": "Conclusions are now grounded in cited evidence and proportionate.", "suggested_next_action": None, "suggested_search_query": None},
            ),
        ],
    }
]

AGENT_INFO = {
    "description": DESCRIPTION,
    "purpose": PURPOSE,
    "prompt_template": PROMPT_TEMPLATE,
    "prompt_examples": PROMPT_EXAMPLES,
}
