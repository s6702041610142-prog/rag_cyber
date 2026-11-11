# Cyber Security Chatbot

Chatbot ที่ตอบคำถามด้าน **penetration testing / cybersecurity** โดยใช้ข้อมูลจาก
`Vyber07/cyber-security` (1 ชุดความรู้เชิงลึก ระดับ PhD) ส่งให้โมเดล **DeepSeek-V4.1-Flash**
ผ่าน **OpenRouter** โดยมี UI เป็น **Chainlit** web chat

> เนื่องจาก dataset นี้เป็นข้อมูลชุดเดียว (ไม่ใช่ Q&A หลายข้อ) จึงส่ง knowledge base
> ทั้งก้อนให้ LLM ตอบตรง ๆ ไม่จำเป็นต้องทำ FAISS/embedding — เบาและเหมาะกับ Render free.

## โครงสร้างโปรเจกต์
```
ragcyber/
├── app_chainlit.py    # Chainlit UI (ตัวหลัก)
├── app.py             # FastAPI JSON API (ทางเลือก, ไม่มี UI)
├── Dockerfile         # Container definition (รัน Chainlit)
├── requirements.txt
├── render.yaml        # Render blueprint (deploy config)
├── .env.example      # ตัวอย่าง environment (คัดลอกเป็น .env)
└── .gitignore        # ไม่ commit .env / token
```

## ⚙️ สิ่งที่ต้องเตรียม
1. สิทธิ์เข้าถึง dataset (gated): https://huggingface.co/datasets/Vyber07/cyber-security
   → ล็อกอิน → **Request access** (จำเป็น แม้มี token ต้องถูกอนุมัติ)
2. HF token: https://huggingface.co/settings/tokens → สร้าง Read token
3. OpenRouter key: https://openrouter.ai/keys

### ไฟล์ `.env` (เครื่อง)
```powershell
copy .env.example .env
```
แล้วแก้ค่า:
```
HF_TOKEN=hf_xxxx
OPENROUTER_API_KEY=sk-or-xxxx
```

## รันบนเครื่อง (ทดสอบ)
```powershell
cd C:\kmutnb\chatbot\ragcyber
pip install -r requirements.txt
python -m chainlit run app_chainlit.py --port 8000
```
เปิด browser ที่ `http://localhost:8000` — web chat พร้อม streaming

หรือใช้ API แบบ JSON (ไม่มี UI):
```powershell
python -m uvicorn app:app --reload --port 8000
```
- `POST /chat` body `{"message":"What is a red team engagement?"}`

## Deploy ขึ้น Render
### ผ่าน Blueprint (แนะนำ)
1. push โปรเจกต์นี้ขึ้น GitHub (เช่น https://github.com/s6702041610142-prog/rag_cyber)
2. Render → **New → Blueprint** → เลือก repo (อ่าน `render.yaml`)
3. นำเข้า env vars: `OPENROUTER_API_KEY`, `HF_TOKEN` (เป็น secret)
4. **Apply** รอ build/deploy → URL จะได้ `https://cyber-chatbot.onrender.com`

### แบบ manual
Render → **New → Web Service** → repo เดียวกัน → runtime `Docker` → เพิ่ม env vars → Deploy

## Environment variables
| ชื่อ | จำเป็น | รายละเอียด |
|---|---|---|
| `OPENROUTER_API_KEY` | ✅ | คีย์ OpenRouter สำหรับตอบคำถาม |
| `HF_TOKEN` | ✅ (ตอนโหลด dataset) | คีย์ HF สำหรับ dataset gated |
| `OPENROUTER_MODEL` | ❌ | ดีฟอลต์ `deepseek/deepseek-v4.1-flash` |
| `DATASET_NAME` | ❌ | ดีฟอลต์ `Vyber07/cyber-security` |

## หมายเหตุ
- **Render free plan** disk/CPU จำกัด — ดีที่ไม่ต้อง build index (cut faiss/torch) image เล็กลงมาก
- ถ้า build ตันเรื่อง disk บน Render ให้เปลี่ยน `plan: free` → `starter` ใน `render.yaml`
- ห้าม commit `.env` จริง ใช้ Render secret env vars แทน
- Chainlit ถูก archive (ไม่มีการ update) แต่ยังใช้ได้ดีกับงานนี้