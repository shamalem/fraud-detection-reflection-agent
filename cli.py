"""CLI entrypoint: run the full agent for one transaction alert.

Usage:
    python -m rag.ingest                              # build the Pinecone index once
    python cli.py --transaction-id TXN_10002
"""
import argparse
import json

from agent.orchestrator import run_agent
from agent.trace import print_trace


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the fraud-triage agent on one transaction.")
    parser.add_argument("--transaction-id", required=True, help="Transaction_ID to look up, e.g. TXN_10002")
    parser.add_argument("--show-trace", action="store_true", help="Print the full step-by-step LLM trace")
    args = parser.parse_args()

    result = run_agent(args.transaction_id)

    print("STATUS:", result["status"])
    print("ERROR:", result["error"])
    print("\nFINAL RESPONSE:")
    print(json.dumps(result["response"], indent=2))
    print("\nNUMBER OF LLM STEPS:", len(result["steps"]))

    if args.show_trace:
        print()
        print_trace(result["steps"])


if __name__ == "__main__":
    main()
