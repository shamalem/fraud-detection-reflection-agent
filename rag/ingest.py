"""One-time build script: extract the fraud-policy PDFs, chunk them, embed, and upload
to Pinecone. Run this once (or after the source PDFs change) - the agent itself only
queries the index (see retriever.py), it never re-embeds the source documents.

Usage:
    python -m rag.ingest
"""
import glob

import tiktoken
from pypdf import PdfReader

from rag.embeddings import embed_texts
from rag.pinecone_client import get_index

# Source PDFs are licensed course material - not committed to this repo. Drop any
# number of them locally under data/raw/ before running; every *.pdf there is
# picked up automatically (exact filenames vary by where each PDF came from, so
# this deliberately doesn't hardcode specific names).
PDF_SOURCE_DIR = "data/raw"

CHUNK_SIZE = 600
CHUNK_OVERLAP = 75
BATCH_SIZE = 20


def extract_pages(pdf_paths: list[str]) -> list[dict]:
    documents = []
    for pdf_path in pdf_paths:
        reader = PdfReader(pdf_path)
        print(pdf_path, "->", len(reader.pages), "pages")

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                documents.append({"source": pdf_path.split("/")[-1], "page": page_number, "text": text.strip()})

    print("Extracted pages:", len(documents))
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    encoding = tiktoken.get_encoding("cl100k_base")
    chunks = []

    for doc in documents:
        tokens = encoding.encode(doc["text"])
        start = 0
        chunk_number = 0

        while start < len(tokens):
            end = min(start + CHUNK_SIZE, len(tokens))
            chunk_text = encoding.decode(tokens[start:end])
            chunks.append({"source": doc["source"], "page": doc["page"], "chunk": chunk_number, "text": chunk_text})

            if end == len(tokens):
                break
            start = end - CHUNK_OVERLAP
            chunk_number += 1

    print("Total chunks:", len(chunks))
    return chunks


def filter_boilerplate(chunks: list[dict]) -> list[dict]:
    """Drop obvious table-of-contents chunks (long runs of dot leaders)."""
    filtered = [c for c in chunks if c["text"].count(".....") <= 3]
    print("Chunks after filtering:", len(filtered))
    return filtered


def upload_chunks(chunks: list[dict]) -> None:
    index = get_index()

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        embeddings = embed_texts(texts)

        vectors = [
            {
                "id": f"fraud_chunk_{start + i}",
                "values": embedding,
                "metadata": {
                    "source": chunk["source"],
                    "page": chunk["page"],
                    "chunk_number": chunk["chunk"],
                    "text": chunk["text"],
                },
            }
            for i, (chunk, embedding) in enumerate(zip(batch, embeddings))
        ]
        index.upsert(vectors=vectors)
        print(f"Uploaded {min(start + BATCH_SIZE, len(chunks))}/{len(chunks)}")


def main() -> None:
    pdf_sources = sorted(glob.glob(f"{PDF_SOURCE_DIR}/*.pdf"))
    if not pdf_sources:
        raise SystemExit(f"No PDFs found under {PDF_SOURCE_DIR}/ - drop the source PDFs there first.")

    documents = extract_pages(pdf_sources)
    chunks = chunk_documents(documents)
    chunks = filter_boilerplate(chunks)
    upload_chunks(chunks)


if __name__ == "__main__":
    main()
