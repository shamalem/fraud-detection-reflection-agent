"""RiskAssessor: drafts the fraud assessment, and re-drafts it after Reflector feedback.

A revision is the RiskAssessor being called again with the reflection appended to its
input - it is logged under the same "RiskAssessor" module name as the initial draft
(not a separate module), so the architecture diagram should show revision as a loop
back into RiskAssessor rather than a distinct box.
"""
import json

from agent.prompts import RISK_ASSESSOR_SYSTEM_PROMPT, build_revision_prompt, build_risk_assessor_prompt
from agent.trace import add_trace_step
from config import settings
from llm.llmod_client import get_client


def call_risk_assessor_llm(state: dict, trace: list) -> dict:
    user_prompt = build_risk_assessor_prompt(state)

    response = get_client().chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": RISK_ASSESSOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    assessment = json.loads(response.choices[0].message.content)

    add_trace_step(
        trace=trace,
        module="RiskAssessor",
        system_prompt=RISK_ASSESSOR_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response=assessment,
    )

    state["draft_assessment"] = assessment
    return assessment


def call_revision_llm(state: dict, trace: list) -> dict:
    user_prompt = build_revision_prompt(state)

    response = get_client().chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": RISK_ASSESSOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    revised_assessment = json.loads(response.choices[0].message.content)

    add_trace_step(
        trace=trace,
        module="RiskAssessor",
        system_prompt=RISK_ASSESSOR_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response=revised_assessment,
    )

    state["draft_assessment"] = revised_assessment
    return revised_assessment
