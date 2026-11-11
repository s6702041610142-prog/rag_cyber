"""Knowledge-base chatbot for the cyber-security dataset served via OpenRouter.
The dataset is a single rich document (PhD-level pentest methodology). We send
the whole dataset as the context to the model; no FAISS/embeddings needed.

API:
  GET /            -> health + doc size
  POST /chat       -> {"message": "..."}  -> {"answer": "..."}

Env:
  OPENROUTER_API_KEY  (required at runtime)
  HF_TOKEN            (only needed to load the dataset at build/startup)
  OPENROUTER_MODEL    (default deepseek/deepseek-v4.1-flash)
"""
import os
import json
from pathlib import Path

import openai
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent
DATASET_NAME = os.environ.get("DATASET_NAME", "Vyber07/cyber-security")
MODEL = os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-v4.1-flash")

app = FastAPI(title="Cyber Security Knowledge Chatbot")

_knowledge: str | None = None


def load_knowledge() -> str:
    """Load the dataset and flatten it into one context string."""
    from datasets import load_dataset
    ds = load_dataset(DATASET_NAME)
    # pick first split (this dataset has a single-row 'test')
    split = next(iter(ds.values()))
    row = split[0]
    return json.dumps(row, ensure_ascii=False, indent=1)


@app.on_event("startup")
def startup():
    global _knowledge
    try:
        _knowledge = load_knowledge()
        print(f"Knowledge loaded ({len(_knowledge)} chars)")
    except Exception as e:
        print(f"WARN: could not load dataset at startup: {e}. "
              "Set HF_TOKEN (needs access to the gated dataset).")


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def root():
    return {"status": "ok", "model": MODEL, "knowledge_chars": len(_knowledge or "")}


@app.post("/chat")
def chat(req: ChatRequest, authorization: str = Header(default=None)):
    if not _knowledge:
        raise HTTPException(status_code=503, detail="Knowledge base not loaded")

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if authorization and authorization.lower().startswith("bearer "):
        api_key = authorization[7:].strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not set")

    client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    system = (
        "You are a senior penetration-testing consultant. Use the provided "
        "knowledge base to answer the user's question. Cite the relevant "
        "methodology/steps when applicable. If the knowledge base lacks an "
        "answer, say so clearly.\n\n"
        "=== KNOWLEDGE BASE ===\n"
        f"{_knowledge}\n"
        "=== END OF KNOWN BADGE ==="
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": req.message},
        ],
        temperature=0.3,
    )
    return {"answer": resp.choices[0].message.content.strip()}