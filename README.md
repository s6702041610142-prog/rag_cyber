# Cyber Security Knowledge Chatbot

Chatbot ที่ตอบคำถามด้าน **penetration testing / cybersecurity** โดยใช้ข้อมูลจาก
`Vyber07/cyber-security` (1 ชุดความรู้เชิงลึก ระดับ PhD) ส่งให้โมเดล **DeepSeek-V4.1-Flash**
ผ่าน **OpenRouter** ตอบเป็นภาษาไทย/อังกฤษ ตามคำถาม

> เพราะ dataset นี้เป็นข้อมูลชุดเดียว (ไม่ใช่ Q&A หลายข้อ) จึงไม่จำเป็นต้องทำ FAISS/embedding
> — ส่ง knowledge base ทั้งก้อนให้ LLM ตอบตรง ๆ ง่ายและเบากว่า เหมาะกับ deploy บน Render free.

## โครงสร้างโปรเจกต์
```
ragcyber/
├── app.py            # FastAPI JSON API (endpoint /chat) ทางเลือก
├── app_chainlit.py   # Chainlit UI (แนะนำ — web chat พร้อม streaming)
├── Dockerfile        # Container definition (รัน Chainlit)
├── requirements.txt
├── render.yaml       # Render blueprint ( deploy config)
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
### 🌐 ใช้ Chainlit UI (แนะนำ)
```powershell
cd C:\kmutnb\chatbot\ragcyber
pip install -r requirements.txt
python -m chainlit run app_chainlit.py --port 8000
```
จากนั้นเปิด browser ที่ `http://localhost:8000` ได้เลย — มี UI แชท สตรีมคำตอบ และ history
- บังคับ login บน Chainlit โดยตั้ง `CHAINLIT_AUTH_SECRET` หรือปิด auth (แบบ dev) ได้

### ใช้ FastAPI (ไม่ต้องการ UI — JSON อย่างเดียว)
```powershell
python -m uvicorn app:app --reload --port 8000
```
- `GET  /` → health + ขนาดความรู้
- `POST /chat` body `{"message":"What is a red team engagement?"}`
  (POST ต้องมี `Authorization: Bearer <OPENROUTER_API_KEY>` หรือตั้ง env ไว้)

## Deploy ขึ้น Render
### ผ่าน Blueprint (ง่ายสุด)
1. push โปรเจกต์นี้ขึ้น GitHub/GitLab
2. Render → **New → Blueprint** → เลือก repo (อ่าน `render.yaml`)
3. กรอก secret env vars: `OPENROUTER_API_KEY`, `HF_TOKEN`
4. **Apply** รอ build
### แบบ manual
Render → **New → Web Service** → รันไทม์ `Docker` → เพิ่ม env vars → Deploy

## Environment variables
| ชื่อ | จำเป็น | รายละเอียด |
|---|---|---|
| `OPENROUTER_API_KEY` | ✅ | คีย์ OpenRouter สำหรับตอบคำถาม |
| `HF_TOKEN` | ✅ (ตอนโหลด dataset) | คีย์ HF สำหรับ dataset gated |
| `OPENROUTER_MODEL` | ❌ | ดีฟอลต์ `deepseek/deepseek-v4.1-flash` |
| `DATASET_NAME` | ❌ | ดีฟอลต์ `Vyber07/cyber-security` |

## หมายเหตุ
- ถ้าอยากได้ RAG (ค้นจากหลายเอกสาร) ต้องเปลี่ยนเป็น dataset ที่มีหลาย rows ก่อน
- Render free plan disk จำกัด — ดีที่ตัด faiss/sentence-transformers ออกแล้ว image จิ๋วลงมาก
- ห้าม commit `.env` จริง ใช้ Render secret env vars แทน