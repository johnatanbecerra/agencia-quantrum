import os
import httpx # Asegúrate de agregar 'httpx' en tu requirements.txt
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Configuración
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TELEGRAM_TOKEN = os.getenv("8811278747:AAG4CxahqUggTd0jx0zXx3ncuIYO163E574", "")
TELEGRAM_CHAT_ID = os.getenv("Quantrum_Clientes_bot", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

class ChatRequest(BaseModel):
    message: str

class ContactoForm(BaseModel):
    nombre: str
    correo: str
    whatsapp: str = ""
    proyecto: str

# Función para enviar alerta por Telegram (100% fiable)
async def enviar_alerta_telegram(datos: ContactoForm):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    texto = (
        f"🔥 **Nuevo Lead Quantrum**\n\n"
        f"👤 *Nombre:* {datos.nombre}\n"
        f"📧 *Email:* {datos.correo}\n"
        f"📱 *WhatsApp:* {datos.whatsapp}\n\n"
        f"💼 *Proyecto:* {datos.proyecto}"
    )
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"})

@app.post("/api/chat")
async def chat_quantrum(req: ChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Falta API KEY de GROQ")
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "Eres el asistente de Quantrum."}, {"role": "user", "content": req.message}],
            model="llama-3.1-8b-instant"
        )
        return {"response": chat_completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/contacto")
async def procesar_contacto(datos: ContactoForm, background_tasks: BackgroundTasks):
    background_tasks.add_task(enviar_alerta_telegram, datos)
    return {"status": "success", "mensaje": "Mensaje enviado a Telegram"}