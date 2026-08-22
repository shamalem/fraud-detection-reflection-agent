"""Execution trace: one entry per LLM call, in the exact shape /api/execute must return."""


def create_trace() -> list:
    return []


def add_trace_step(trace: list, module: str, system_prompt: str, user_prompt: str, response: dict) -> None:
    trace.append(
        {
            "module": module,
            "prompt": {"system_prompt": system_prompt, "user_prompt": user_prompt},
            "response": response,
        }
    )


def print_trace(trace: list) -> None:
    for i, step in enumerate(trace, start=1):
        print("=" * 80)
        print(f"STEP {i}")
        print("Module:", step["module"])
        print("\nSYSTEM PROMPT:")
        print(step["prompt"]["system_prompt"])
        print("\nUSER PROMPT:")
        print(step["prompt"]["user_prompt"])
        print("\nRESPONSE:")
        print(step["response"])
