"""Planner: chooses the single next action given the current investigation state."""
import json

from agent.prompts import PLANNER_SYSTEM_PROMPT, build_planner_prompt
from agent.trace import add_trace_step
from config import settings
from llm.llmod_client import get_client


def call_planner_llm(state: dict, trace: list) -> dict:
    user_prompt = build_planner_prompt(state)

    response = get_client().chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    decision = json.loads(response.choices[0].message.content)

    add_trace_step(
        trace=trace,
        module="Planner",
        system_prompt=PLANNER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response=decision,
    )

    return decision
