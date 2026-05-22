import os
import httpx
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
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

class ChatRequest(BaseModel):
    message: str

class ContactoForm(BaseModel):
    nombre: str
    correo: str
    whatsapp: str = ""
    proyecto: str

# Función para enviar alerta por Telegram
async def enviar_alerta_telegram(datos: ContactoForm):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    texto = (
        f"🔥 **Nuevo Lead Quantrum**\n\n"
        f"👤 *Nombre:* {datos.nombre}\n"
        f"📧 *Email:* {datos.correo}\n"
        f"📱 *WhatsApp:* {datos.whatsapp}\n\n"
        f"💼 *Proyecto:* {datos.proyecto}"
    )
    try:
        async with httpx.AsyncClient() as client_http:
            await client_http.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"Error Telegram: {e}")

@app.post("/api/chat")
async def chat_quantrum(req: ChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Falta API KEY de GROQ")
    
    # --- AQUÍ ESTÁ EL CAMBIO DE LÓGICA ---
    system_instruction = """
    Eres 'Chat Quantrum Pro', el asistente virtual de QUANTRUM, una Agencia Digital de Élite. 
    Eres un consultor experto y profesional.
    
    Tus reglas estrictas de comunicación:
    1. Nunca menciones tiempos de creación en 'segundos o minutos'. Eso resta valor profesional a nuestro trabajo artesanal.
    2. Cuando pregunten por tiempos de entrega, responde siempre así: 'En Quantrum, la calidad y el detalle son nuestra prioridad. Por lo general, un proyecto web profesional toma entre 1 a 2 semanas para cobrar vida, estar totalmente optimizado y listo para mostrarse al mundo con el mayor impacto.'
    3. Enfatiza que cada desarrollo es personalizado, robusto y escalable.
    4. Responde siempre de forma profesional, clara, concisa y orientada a la venta.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": req.message}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.4
        )
        return {"response": chat_completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/contacto")
async def procesar_contacto(datos: ContactoForm, background_tasks: BackgroundTasks):
    background_tasks.add_task(enviar_alerta_telegram, datos)
    return {"status": "success", "mensaje": "Mensaje enviado"}