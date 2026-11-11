"""Gradio UI for the cyber-security knowledge chatbot.
Run:  python app_gradio.py               # local
Deploy on Render via Dockerfile (CMD runs this app).
"""
import json
import os
import gradio as gr
import openai

DATASET_NAME = os.environ.get("DATASET_NAME", "Vyber07/cyber-security")
MODEL = os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-v4.1-flash")

_knowledge: str | None = None


def load_knowledge() -> str:
    from datasets import load_dataset
    ds = load_dataset(DATASET_NAME)
    split = next(iter(ds.values()))
    row = split[0]
    return json.dumps(row, ensure_ascii=False, indent=1)


def chat(message, history):
    global _knowledge
    if _knowledge is None:
        try:
            _knowledge = load_knowledge()
        except Exception as e:
            _knowledge = "ERROR"
            return f"⚠️ Could not load dataset: {e}\nSet HF_TOKEN (gated dataset access required)."

    if _knowledge == "ERROR":
        return "Knowledge base unavailable. Restart server with HF_TOKEN set."

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return "⚠️ OPENROUTER_API_KEY is not set."

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
                {"role": "user", "content": message},
            ],
            temperature=0.3,
            stream=True,
        )
        full = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full += delta
                yield full
    except Exception as e:
        yield f"⚠️ Error from model: {e}"


TITLE = "🛡️ Cyber Security Chatbot"
DESC = (
    "ถามคำถามเกี่ยวกับ penetration testing / cybersecurity ได้เลย "
    "ตอบจาก knowledge base โดย DeepSeek-V4.1-Flash ผ่าน OpenRouter"
)

# Gradio 6: ChatInterface has no `theme` arg; wrap it in Blocks to apply a theme.
with gr.Blocks(title=TITLE, theme=gr.themes.Soft()) as demo:
    gr.Markdown(f"# {TITLE}\n{DESC}")
    demo_chat = gr.ChatInterface(
        fn=chat,
        title=TITLE,
        description=DESC,
        concurrency_limit=3,
        save_history=True,
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    demo.queue().launch(server_name="0.0.0.0", server_port=port)