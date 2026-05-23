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
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Faltan TELEGRAM_TOKEN o TELEGRAM_CHAT_ID en Render")
        return

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
            response = await client_http.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "Markdown"})
            if response.status_code == 200:
                print("Telegram enviado con éxito")
            else:
                print(f"Error Telegram: {response.text}")
    except Exception as e:
        print(f"Error crítico enviando Telegram: {str(e)}")

@app.post("/api/chat")
async def chat_quantrum(req: ChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Falta API KEY de GROQ")
    
    # --- REGLAS ESTRICTAS DE CONTROL ---
    system_instruction = """
    Eres 'Chat Quantrum Pro', el asistente virtual de QUANTRUM, una Agencia Digital de Élite. 
    Eres un consultor experto, serio y profesional.
    
    Tus reglas de comunicación inquebrantables:
    1. TIEMPOS: Nunca menciones tiempos de creación en 'segundos o minutos'. Responde siempre: 'Por lo general, un proyecto web profesional toma entre 1 a 2 semanas para cobrar vida, estar totalmente optimizado y listo para mostrarse al mundo.'
    2. PRECIOS DE DESARROLLO Y DISEÑO: Tienes estrictamente PROHIBIDO inventar precios altos de miles de dólares (como $2500, $4500 o $7000). Si te preguntan cuánto cuesta una página web o un rediseño, responde: 'En Quantrum ofrecemos planes muy accesibles y competitivos. Como cada proyecto es único, preferimos ajustarnos a tus necesidades. ¡Déjanos tus datos en el formulario o escríbenos al WhatsApp y un asesor te dará una cotización excelente hoy mismo!'
    3. PRECIOS DE HOSTING: Los únicos precios exactos que puedes dar son los de nuestros servidores: Plan Startup ($10/mes), Business ($25/mes) y Enterprise ($60/mes).
    4. ENFOQUE: Enfatiza que cada desarrollo es personalizado, robusto y escalable.
    5. CONTACTO REAL DE WHATSAPP (MÁXIMA PRIORIDAD): Si el cliente te pide nuestro número de WhatsApp o pregunta cómo contactarnos de forma directa, debes proporcionarle ÚNICAMENTE nuestros números oficiales de Venezuela: (+58) 412-9550884 y (+58) 426-5336973. Queda terminantemente PROHIBIDO inventar cualquier otro prefijo internacional o número de teléfono.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": req.message}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3
        )
        return {"response": chat_completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/contacto")
async def procesar_contacto(datos: ContactoForm, background_tasks: BackgroundTasks):
    background_tasks.add_task(enviar_alerta_telegram, datos)
    return {"status": "success", "mensaje": "Mensaje enviado"}