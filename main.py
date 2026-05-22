import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

# 1. CREACIÓN DE LA APP (Debe ir siempre arriba)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# 2. CONFIGURACIÓN DE IA (GROQ)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# 3. ESTRUCTURAS DE DATOS
class ChatRequest(BaseModel):
    message: str

class ContactoForm(BaseModel):
    nombre: str
    correo: str
    whatsapp: str = ""
    proyecto: str

# 4. FUNCIÓN PARA ENVIAR CORREO (EN SEGUNDO PLANO)
def enviar_alerta_correo(datos: ContactoForm):
    remitente = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")
    servidor_smtp = os.environ.get("SMTP_SERVER", "mail.quantrum1.com")
    puerto = int(os.environ.get("SMTP_PORT", 465))

    if not remitente or not password:
        print("Error: Faltan credenciales de correo en Render")
        return

    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = f"🔥 Nuevo Lead Quantrum: {datos.nombre}"
    mensaje["From"] = remitente
    mensaje["To"] = remitente

    texto = f"""
    ¡Tienes un nuevo cliente potencial!
    
    👤 Nombre: {datos.nombre}
    📧 Email: {datos.correo}
    📱 WhatsApp: {datos.whatsapp}
    
    💼 Proyecto / Mensaje:
    {datos.proyecto}
    """
    
    parte_texto = MIMEText(texto, "plain")
    mensaje.attach(parte_texto)

    try:
        if puerto == 465:
            server = smtplib.SMTP_SSL(servidor_smtp, puerto)
        else:
            server = smtplib.SMTP(servidor_smtp, puerto)
            server.starttls()
            
        server.login(remitente, password)
        server.sendmail(remitente, remitente, mensaje.as_string())
        server.quit()
        print("Correo enviado con éxito")
    except Exception as e:
        print(f"Error SMTP: {e}")

# 5. RUTAS / ENDPOINTS (Van al final)

# Endpoint del Chatbot
@app.post("/api/chat")
async def chat_quantrum(req: ChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Falta API KEY de GROQ")
        
    system_instruction = "Eres 'Chat Quantrum Pro', el asistente virtual de QUANTRUM, una Agencia Digital de Élite. Responde de forma profesional, clara y concisa."
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": req.message}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.4
        )
        return {"response": chat_completion.choices[0].message.content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint del Formulario de Contacto
@app.post("/api/contacto")
async def procesar_contacto(datos: ContactoForm, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(enviar_alerta_correo, datos)
        return {"status": "success", "mensaje": "Mensaje recibido"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error procesando el formulario")