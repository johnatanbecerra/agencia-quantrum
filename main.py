import os
import urllib.request
import urllib.error
import json
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://placeholder-url.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "placeholder-key")
# TU CLAVE REAL INYECTADA
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
        return {"response": "Requiero una API Key real."}
    
    # URL CORREGIDA: Apuntando al modelo exacto para evitar el Error 404
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    system_instruction = "Eres 'Chat Quantrum Pro', el asistente virtual de Inteligencia Artificial exclusivo de la agencia digital QUANTRUM. Tu única tarea es orientar de forma sumamente breve, concisa y cortés (máximo 2 a 3 líneas por respuesta) a los clientes. Habla sobre nuestros servicios: Web, PWA, UI/UX, E-Commerce, SEO y APIs. Si preguntan precios, indica que cotizamos a medida e invita a usar WhatsApp. Responde en español, profesional y tecnológico."
    
    payload = {
        "contents": [{"parts": [{"text": req.message}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {"maxOutputTokens": 150, "temperature": 0.4}
    }
    req_data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=req_data, headers={"Content-Type": "application/json"}, method="POST")

    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                return {"response": res_body['candidates'][0]['content']['parts'][0]['text'].strip()}
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep((2 ** attempt) + 1)
                continue
            
            # CAPTURA EL ERROR REAL DE GOOGLE
            error_msg = e.read().decode("utf-8")
            try:
                error_json = json.loads(error_msg)
                real_message = error_json.get("error", {}).get("message", "Error desconocido")
            except:
                real_message = error_msg
                
            return {"response": f"Código {e.code}: {real_message}"}
            
        except Exception as e:
            return {"response": f"Fluctuación en el canal local: {str(e)}"}
            
    return {"response": "Error de conexión temporal tras múltiples intentos."}

@app.get("/")
async def read_index(): return FileResponse('index.html')
@app.get("/manifest.json")
async def read_manifest(): return FileResponse('manifest.json')
@app.get("/sw.js")
async def read_sw(): return FileResponse('sw.js')
app.mount("/", StaticFiles(directory="."), name="static")