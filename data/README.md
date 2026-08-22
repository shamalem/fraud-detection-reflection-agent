# Data

The agent has no local dataset - all transaction data lives in **Supabase**
(table configured via `SUPABASE_TABLE`, default `fraud_dataset`) and all fraud-policy
knowledge lives in **Pinecone** (index configured via `PINECONE_INDEX`, default
`fraud-agent`). This directory only documents the schemas; nothing here is loaded
by the running agent.

## Supabase: `fraud_dataset` table

Columns actually read by `db/supabase_client.py`:

`Transaction_ID, User_ID, Timestamp, Transaction_Amount, Transaction_Type, Location,
Device_Type, IP_Address_Flag, Previous_Fraudulent_Activity, Failed_Transaction_Count_7d,
Authentication_Method`

`Fraud_Label` (if present) is ground truth and is never shown to the LLM roles.

## Pinecone: `fraud-agent` index

Built by `rag/ingest.py` (`python -m rag.ingest`) from three licensed source PDFs,
chunked at 600 tokens (75 overlap) and embedded with `EMBED_MODEL`:

- Mastercard *Security Rules and Procedures - Merchant Edition* (12 pages)
- Mastercard transaction-processing rules (26 pages)
- ECB *Seventh report on card fraud* (15 pages)

These PDFs are licensed course material and are **not committed to this repo** - drop
however many you have, under any filename, into `data/raw/` before running the ingest
script; every `*.pdf` found there is picked up automatically (extraction verified
locally: all 53 pages extract cleanly). The index itself, once built, is what the
running agent queries; the source PDFs are only needed to (re)build it.
