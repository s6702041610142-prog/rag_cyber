"""Chainlit UI for the cyber-security knowledge chatbot.
Run:  chainlit run app_chainlit.py --port 8000
Uses the same dataset knowledge base + OpenRouter logic as app.py.
Deployable on Render via Dockerfile (CMD runs chainlit).
"""
import json
import os
from pathlib import Path

import chainlit as cl
import openai

BASE_DIR = Path(__file__).parent
DATASET_NAME = os.environ.get("DATASET_NAME", "Vyber07/cyber-security")
MODEL = os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-v4.1-flash")

_knowledge: str | None = None


def load_knowledge() -> str:
    from datasets import load_dataset
    ds = load_dataset(DATASET_NAME)
    split = next(iter(ds.values()))
    row = split[0]
    return json.dumps(row, ensure_ascii=False, indent=1)


@cl.on_chat_start
async def on_start():
    global _knowledge
    try:
        _knowledge = load_knowledge()
        await cl.Message(
            content=f"✅ Knowledge base loaded ({len(_knowledge)} chars).\n"
                    "Ask me anything about penetration testing / cybersecurity."
        ).send()
    except Exception as e:
        _knowledge = None
        await cl.Message(
            content=f"⚠️ Could not load the dataset: {e}\n"
                    "Set HF_TOKEN (needs access to the gated dataset)."
        ).send()


@cl.on_message
async def on_message(message: cl.Message):
    if not _knowledge:
        await cl.Message(content="Knowledge base not available yet. Try again later.").send()
        return
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        await cl.Message(content="OPENROUTER_API_KEY is not set.").send()
        return
    client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    system = (
        "You are a senior penetration-testing consultant. Answer using the "
        "provided knowledge base. Cite relevant methodology/steps. If the "
        "knowledge base lacks an answer, say so clearly.\n\n"
        "=== KNOWLEDGE BASE ===\n"
        f"{_knowledge}\n"
        "=== END ==="
    )
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": message.content},
        ],
        temperature=0.3,
        stream=True,
    )
    full = ""
    msg = cl.Message(content="")
    await msg.send()
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            full += delta
            await msg.stream_token(delta)
    await msg.update()