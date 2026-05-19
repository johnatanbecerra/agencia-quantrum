import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from supabase import create_client, Client
from groq import Groq

app = FastAPI()

# --- CONFIGURACIÓN DE CORS PARA PERMITIR CONEXIÓN DESDE GITHUB PAGES ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://placeholder-url.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "placeholder-key")

# AQUÍ LE DECIMOS QUE BUSQUE LA CLAVE OCULTA EN EL SERVIDOR
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

supabase = None
try:
    if SUPABASE_URL and not SUPABASE_URL.startswith("https://placeholder"):
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Conexión a Supabase configurada.")
    else:
        print("⚠ Supabase en modo simulación.")
except Exception as e:
    print(f"⚠ Error Supabase: {e}")

# --- INICIALIZACIÓN OFICIAL DEL CLIENTE DE GROQ ---
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

class ContactoForm(BaseModel):
    nombre: str; correo: str; whatsapp: str; proyecto: str

class ChatRequest(BaseModel):
    message: str

@app.post("/api/contacto")
async def recibir_contacto(form: ContactoForm):
    if supabase:
        try:
            supabase.table("contactos").insert({"nombre": form.nombre, "correo": form.correo, "whatsapp": form.whatsapp, "proyecto": form.proyecto}).execute()
            return {"status": "success"}
        except Exception: return {"status": "error"}
    return {"status": "success"}

@app.post("/api/chat")
async def chat_quantrum(req: ChatRequest):
    if not GROQ_API_KEY:
        return {"response": "API Key de Groq no configurada en las variables de entorno de Render."}
        
    if not client:
        return {"response": "Error al inicializar el cliente de Groq."}
    
    system_instruction = (
        "Eres 'Chat Quantrum Pro', el asistente virtual de Inteligencia Artificial exclusivo de la "
        "agencia digital QUANTRUM. Tu única tarea es orientar de forma sumamente breve, concisa y cortés "
        "(máximo 2 a 3 líneas por respuesta) a los clientes. Habla sobre nuestros servicios: Web, PWA, "
        "UI/UX, E-Commerce, SEO y APIs. Si preguntan precios, indica que cotizamos a medida e invita a usar WhatsApp. "
        "Responde siempre en español, con un tono profesional, persuasivo y tecnológico."
    )
    
    try:
        # Petición oficial a los servidores de Groq utilizando Llama 3
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": req.message}
            ],
            model="llama3-8b-8192",  # Libre de bloqueos para Venezuela
            temperature=0.4,
            max_tokens=150,
        )
        return {"response": chat_completion.choices[0].message.content.strip()}
    except Exception as e:
        return {"response": f"Error de enlace en la IA: {str(e)}"}

@app.get("/")
async def read_index(): return FileResponse('index.html')
@app.get("/manifest.json")
async def read_manifest(): return FileResponse('manifest.json')
@app.get("/sw.js")
async def read_sw(): return FileResponse('sw.js')
app.mount("/", StaticFiles(directory="."), name="static")