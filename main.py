import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from supabase import create_client, Client
import google.generativeai as genai

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
# CLAVE DE GOOGLE GEMINI INYECTADA
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBkdJpMrjmCacqk2ol4D0KSuMrkRnV88yA")

supabase = None
try:
    if SUPABASE_URL and not SUPABASE_URL.startswith("https://placeholder"):
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Conexión a Supabase configurada.")
    else:
        print("⚠ Supabase en modo simulación.")
except Exception as e:
    print(f"⚠ Error Supabase: {e}")

# --- CONFIGURACIÓN GLOBAL DEL SDK DE GEMINI ---
if GEMINI_API_KEY and len(GEMINI_API_KEY) > 20:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("⚠ Error: API Key de Gemini no configurada correctamente.")

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
    if not GEMINI_API_KEY or len(GEMINI_API_KEY) < 20:
        return {"response": "API Key de Gemini no detectada."}
    
    system_instruction = (
        "Eres 'Chat Quantrum Pro', el asistente virtual de Inteligencia Artificial exclusivo de la "
        "agencia digital QUANTRUM. Tu única tarea es orientar de forma sumamente breve, concisa y cortés "
        "(máximo 2 a 3 líneas por respuesta) a los clientes. Habla sobre nuestros servicios: Web, PWA, "
        "UI/UX, E-Commerce, SEO y APIs. Si preguntan precios, indica que cotizamos a medida e invita a usar WhatsApp. "
        "Responde siempre en español, con un tono profesional, elegante y tecnológico."
    )
    
    try:
        # Inicialización forzada y única con gemini-1.5-flash y sus instrucciones de sistema
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_instruction
        )
        
        # Generación de contenido limpia mediante el SDK oficial
        response = model.generate_content(req.message)
        return {"response": response.text.strip()}
        
    except Exception as e:
        return {"response": f"Error de configuración en la IA: {str(e)}"}

@app.get("/")
async def read_index(): return FileResponse('index.html')
@app.get("/manifest.json")
async def read_manifest(): return FileResponse('manifest.json')
@app.get("/sw.js")
async def read_sw(): return FileResponse('sw.js')
app.mount("/", StaticFiles(directory="."), name="static")