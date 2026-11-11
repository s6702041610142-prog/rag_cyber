"""Chainlit UI for the cyber-security knowledge chatbot.
Run:  chainlit run app_chainlit.py --port 8000
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

# ---- Example starter questions shown on the welcome screen ----
EXAMPLE_STARTERS = [
    "What is the difference between black box and white box testing?",
    "List the phases of PTES penetration testing.",
    "What is a red team engagement?",
    "Which OWASP testing categories exist?",
    "What certifications are relevant for web security?",
]


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
        greet = (
            "🛡️ **Cyber Security Assistant**\n\n"
            f"ยินดีต้อนรับ! Knowledge base โหลดแล้ว ({len(_knowledge):,} chars)\n"
            "ลองถามคำถามเกี่ยวกับ penetration testing / cybersecurity ด้านล่างได้เลย 👇"
        )
        await cl.Message(content=greet).send()
        # Show clickable example starters (use payload, not value — Action has no 'value' field)
        actions = [
            cl.Action(name=f"starter_{i}", payload={"q": q}, label=q)
            for i, q in enumerate(EXAMPLE_STARTERS)
        ]
        await cl.Message(content="**ตัวอย่างคำถาม:**", actions=actions).send()
    except Exception as e:
        _knowledge = None
        await cl.Message(
            content=f"⚠️ Could not load the dataset: {e}\n"
                    "Set HF_TOKEN (needs access to the gated dataset)."
        ).send()


@cl.action_callback("starter_0")
async def on_starter0(action: cl.Action): await handle_starter(action)
@cl.action_callback("starter_1")
async def on_starter1(action: cl.Action): await handle_starter(action)
@cl.action_callback("starter_2")
async def on_starter2(action: cl.Action): await handle_starter(action)
@cl.action_callback("starter_3")
async def on_starter3(action: cl.Action): await handle_starter(action)
@cl.action_callback("starter_4")
async def on_starter4(action: cl.Action): await handle_starter(action)


async def handle_starter(action: cl.Action):
    # Action has no 'value' field; the question is carried in payload dict.
    question = action.payload.get("q") if isinstance(action.payload, dict) else str(action.payload)
    if not question:
        await cl.Message(content="⚠️ Invalid starter action.").send()
        return
    await cl.Message(content=question, author="You").send()
    await answer(question)


@cl.on_message
async def on_message(message: cl.Message):
    await answer(message.content)


async def answer(question: str):
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
    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": question},
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
    except Exception as e:
        await cl.Message(content=f"⚠️ Error from model: {e}").send()