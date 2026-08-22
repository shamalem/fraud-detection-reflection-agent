"""run_agent: the full Planner -> Tools/RAG -> RiskAssessor -> Reflector -> revision loop.

Returns exactly {status, error, response, steps} - the shape required by POST /api/execute.
"""
import time

from agent.planner import call_planner_llm
from agent.reflector import call_reflector_llm
from agent.risk_assessor import call_revision_llm, call_risk_assessor_llm
from agent.state import create_agent_state
from agent.tools import TOOLS, run_selected_tool, update_state_from_tool
from agent.trace import create_trace
from config import settings


def run_agent(transaction_id: str) -> dict:
    state = create_agent_state(transaction_id)
    trace = create_trace()

    planner_iterations = 0
    reflection_cycles = 0
    reflection_decision = None
    start_time = time.monotonic()

    def _time_budget_exceeded() -> bool:
        return time.monotonic() - start_time >= settings.max_wall_clock_seconds

    def _time_budget_response() -> dict:
        # maxDuration only raises the ceiling Vercel allows; it does not stop Vercel
        # from killing the request with no response at all once that ceiling is hit.
        # This returns whatever we have with time to spare, so the client still gets
        # a clean {status, response, steps} instead of a raw platform timeout.
        if state["draft_assessment"] is not None:
            state["draft_assessment"]["review_status"] = "unreviewed_time_budget_exceeded"
            state["final_answer"] = state["draft_assessment"]
            return {"status": "ok", "error": None, "response": state["final_answer"], "steps": trace}
        return {
            "status": "error",
            "error": "Agent exceeded its time budget before producing an assessment.",
            "response": None,
            "steps": trace,
        }

    try:
        while planner_iterations < settings.max_planner_iterations:
            if _time_budget_exceeded():
                return _time_budget_response()

            state["iteration"] = planner_iterations + 1

            # 1. PLANNER
            decision = call_planner_llm(state, trace)
            action = decision.get("action")
            arguments = decision.get("arguments", {})

            # 2. PLANNER CHOOSES ASSESS
            if action == "assess":
                call_risk_assessor_llm(state, trace)

                # 3. REFLECTION LOOP
                while reflection_cycles < settings.max_reflection_cycles:
                    if _time_budget_exceeded():
                        return _time_budget_response()

                    reflection = call_reflector_llm(state, trace)
                    reflection_decision = reflection.get("decision")

                    if reflection_decision == "APPROVE":
                        state["draft_assessment"]["review_status"] = "approved"
                        state["final_answer"] = state["draft_assessment"]
                        return {"status": "ok", "error": None, "response": state["final_answer"], "steps": trace}

                    elif reflection_decision == "REVISE":
                        reflection_cycles += 1
                        call_revision_llm(state, trace)
                        continue

                    elif reflection_decision == "NEED_MORE_EVIDENCE":
                        reflection_cycles += 1
                        if reflection_cycles >= settings.max_reflection_cycles:
                            # Budget's about to run out right when the Reflector said
                            # the draft wasn't grounded enough - force one revision
                            # before shipping it, instead of returning it as-is.
                            call_revision_llm(state, trace)
                        break  # return control to Planner

                    else:
                        raise ValueError(f"Unknown reflection decision: {reflection_decision}")

                # Reflection limit reached - ship the latest revised assessment, but be
                # honest that it was never a fully-reviewed APPROVE. A cap hit right after
                # NEED_MORE_EVIDENCE is worse than one hit after REVISE: the Reflector didn't
                # just find flaws to fix, it said there wasn't enough evidence to judge at all -
                # even with one forced revision attempt above, no Reflector ever re-checked it.
                if reflection_cycles >= settings.max_reflection_cycles:
                    state["draft_assessment"]["review_status"] = (
                        "unreviewed_insufficient_evidence"
                        if reflection_decision == "NEED_MORE_EVIDENCE"
                        else "unreviewed_revision_limit_reached"
                    )
                    state["final_answer"] = state["draft_assessment"]
                    return {"status": "ok", "error": None, "response": state["final_answer"], "steps": trace}

                # NEED_MORE_EVIDENCE returned us here; Planner gets the updated state + reflection.
                planner_iterations += 1
                continue

            # 4. PLANNER CHOOSES A TOOL
            if action not in TOOLS:
                raise ValueError(f"Unknown Planner action: {action}")

            result = run_selected_tool(action, arguments)

            if isinstance(result, dict) and "error" in result:
                raise RuntimeError(f"Tool {action} failed: {result['error']}")

            # A missing target transaction is not sparse evidence to reason around - it
            # means the request has no subject at all, so stop immediately rather than
            # letting the Planner proceed to an assessment with nothing to assess.
            if action == "get_transaction" and result is None:
                return {
                    "status": "error",
                    "error": f"No transaction found with ID '{transaction_id}'.",
                    "response": None,
                    "steps": trace,
                }

            update_state_from_tool(state, action, result)
            planner_iterations += 1

        # 5. PLANNER SAFETY LIMIT
        if state["draft_assessment"] is not None:
            state["draft_assessment"]["review_status"] = "unreviewed_planner_iteration_limit_reached"
            state["final_answer"] = state["draft_assessment"]
            return {"status": "ok", "error": None, "response": state["final_answer"], "steps": trace}

        return {
            "status": "error",
            "error": "Agent reached the maximum investigation iterations before producing an assessment.",
            "response": None,
            "steps": trace,
        }

    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {e}", "response": None, "steps": trace}
