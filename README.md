# Fraud Detection Reflection Agent

An autonomous fraud-triage agent for one transaction alert at a time. A **Planner**
decides, one step at a time, which tool to call next (no fixed sequence); once it has
enough evidence it hands off to a **RiskAssessor**, which drafts a structured risk
assessment; a **Reflector** audits that draft against the same evidence and either
approves it, sends it back for revision, or asks the Planner to gather more evidence.

```
Planner (chooses: get_transaction / get_user_summary / get_recent_user_transactions
         / search_fraud_knowledge / assess)
   |
   v
RiskAssessor -> draft assessment
   |
   v
Reflector -> APPROVE            -> done
           -> REVISE            -> RiskAssessor drafts again (same module, new input)
           -> NEED_MORE_EVIDENCE -> back to Planner
```

Built for the "Fraud Detection & Risk Analysis" domain: small fintech fraud analysts
drowning in alerts (up to ~95% of AML alerts are false positives), needing a
grounded, explainable first pass before a human reviews the case.

## Status

Ported from the working notebook (`Agent.ipynb`) into proper application modules.
The agent logic, tools, and prompts are unchanged from the tested notebook version.
The `/api/*` endpoints, architecture diagram, GUI, and Vercel config are all in place
(see below). `server/team_info.py` has all three team emails filled in.

## Deployment (Vercel)

- Root `index.html` is the GUI (static, no build step, no auth).
- **Single Python entrypoint**: Vercel's Python runtime on this account expects exactly
  one entrypoint per project (declared in `pyproject.toml`), not one function per file
  under `api/`. `api/index.py` is a small Flask app that serves all four `/api/*` routes
  internally; `vercel.json` rewrites every `/api/*` request to it. The route logic itself
  lives in `server/` (kept outside `api/` so those files aren't picked up as additional
  entrypoint candidates).
- `vercel.json` also sets `maxDuration: 300` on `/api/index.py` (Vercel's serverless cap).
- The CLI script is named `cli.py`, not `main.py` - a root-level `main.py`/`app.py` is
  treated as an implicit function entrypoint too and broke the build the same way.
  Keep it `cli.py`.

## Architecture (code layout)

```
index.html                     GUI - static, calls POST /api/execute
cli.py                          CLI entrypoint - runs the agent for one Transaction_ID
config.py                      Settings, read from env vars / .env
pyproject.toml                 [project] deps only - no [tool.vercel] entrypoint (see below)
vercel.json                    /api/* rewrites + maxDuration config

api/
  index.py                     The one Vercel entrypoint - Flask app, all 4 routes

server/
  team_info.py                 Data for GET /api/team_info
  agent_info.py                Data for GET /api/agent_info
  execute.py                   handle_prompt() for POST /api/execute

assets/
  model_architecture.png       Architecture diagram, served by GET /api/model_architecture
                                (module names match the trace exactly)

agent/
  state.py                     create_agent_state, AGENT_ACTIONS, AGENT_DECISION_SCHEMA
  prompts.py                   System prompts + user-prompt builders for all three roles
  trace.py                     create_trace / add_trace_step / print_trace
  tools.py                     TOOLS registry, execute_tool, update_state_from_tool
  planner.py                   call_planner_llm - chooses the next action
  risk_assessor.py             call_risk_assessor_llm, call_revision_llm
  reflector.py                 call_reflector_llm - APPROVE / REVISE / NEED_MORE_EVIDENCE
  orchestrator.py              run_agent - the full loop, returns {status, error, response, steps}

llm/
  llmod_client.py               LLMod.ai client (OpenAI-compatible chat + embeddings)

db/
  supabase_client.py            get_transaction, get_user_transactions,
                                 get_recent_user_transactions, get_user_summary

rag/
  pinecone_client.py            Pinecone index connection
  embeddings.py                 embed_texts() via LLMod
  retriever.py                  search_fraud_knowledge() - Planner writes the query itself
  ingest.py                     One-time PDF -> chunks -> Pinecone upload script

data/
  README.md                     Supabase table schema + RAG source documents (not committed)
```

## Data sources

- **Transactions** — Supabase table `fraud_dataset`. No local copy; see `data/README.md`
  for the columns the agent actually reads.
- **Fraud-policy knowledge** — Pinecone index `fraud-agent`, built from three licensed
  PDFs (Mastercard SPME manual, Mastercard transaction-processing rules, ECB's *Seventh
  report on card fraud*) via `rag/ingest.py`. The PDFs themselves aren't committed
  (licensed course material) - only the code to (re)build the index from them.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in LLMOD_API_KEY, SUPABASE_URL/SUPABASE_SECRET_KEY, PINECONE_API_KEY
```

## Usage

```bash
# 1. (once, or after the source PDFs change) build the Pinecone index
python -m rag.ingest

# 2. Run the agent on one transaction
python cli.py --transaction-id TXN_10002 --show-trace
```

Prints the final structured assessment plus, with `--show-trace`, every LLM step
(module, system prompt, user prompt, response) in the order they ran.

## Example Test Prompts

**1. Reflection loop catches and corrects overclaims**
```
Investigate TXN_27094 for potential fraud and give me a clear verdict — is this safe to approve, or does something here warrant a hold?
```
The first draft overclaimed twice (treating a general ECB statistic as transaction-specific proof, and treating sparse history as a risk factor instead of an uncertainty). The Reflector caught both, sent it back for revision twice, and the agent converged on `risk_level: "low"` with `confidence: 0.38` — a real, earned verdict, not a default "medium."

**2. Explicit dataset signals correctly drive risk up**
```
Analyze TXN_16957 for fraud risk and explain what action should be taken.
```
This transaction has both `IP_Address_Flag = 1` and `Previous_Fraudulent_Activity = 1` — the only two fields the grounding rules allow to be read as fraud signals directly. The agent correctly elevates risk on that basis, while the Reflector strips out an unsupported claim about geographic distance from the draft, landing on `risk_level: "medium"` with a proportional "manual review" recommendation.

**3. Nonexistent transaction ID**
```
Investigate transaction TXN_00000000.
```
Returns the spec-required error shape immediately, with no fabricated assessment:
```json
{ "status": "error", "error": "No transaction found with ID 'TXN_00000000'.", "response": null, "steps": [] }
```

## Configuration

All settings are env vars, see `.env.example`:

| Variable | Purpose |
|---|---|
| `LLMOD_API_KEY`, `LLMOD_BASE_URL` | Course-issued LLMod.ai credentials |
| `CHAT_MODEL`, `EMBED_MODEL` | Must match the course spec exactly (`MB5R2CF-azure/...`) |
| `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SUPABASE_TABLE` | Transaction database |
| `PINECONE_API_KEY`, `PINECONE_INDEX`, `RETRIEVAL_TOP_K` | Fraud-policy vector index |
| `MAX_PLANNER_ITERATIONS`, `MAX_REFLECTION_CYCLES` | Loop safety limits |
