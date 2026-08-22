"""Reflector: audits the draft assessment and decides APPROVE / REVISE / NEED_MORE_EVIDENCE."""
import json

from agent.prompts import REFLECTOR_SYSTEM_PROMPT, build_reflector_prompt
from agent.trace import add_trace_step
from config import settings
from llm.llmod_client import get_client


def call_reflector_llm(state: dict, trace: list) -> dict:
    user_prompt = build_reflector_prompt(state)

    response = get_client().chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": REFLECTOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    reflection = json.loads(response.choices[0].message.content)

    add_trace_step(
        trace=trace,
        module="Reflector",
        system_prompt=REFLECTOR_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response=reflection,
    )

    state["reflection"] = reflection
    return reflection
