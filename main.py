import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI()

# Configuración segura de Supabase para evitar caídas de servidor
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://placeholder-url.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "placeholder-key")

supabase = None
try:
    if SUPABASE_URL and not SUPABASE_URL.startswith("https://placeholder"):
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Conexión a Supabase configurada con éxito.")
    else:
        print("⚠ Supabase en modo simulación (Faltan credenciales válidas).")
except Exception as e:
    print(f"⚠ Error al inicializar Supabase, continuando en modo simulación: {e}")

class ContactoForm(BaseModel):
    nombre: str
    correo: str
    whatsapp: str
    proyecto: str

@app.post("/api/contacto")
async def recibir_contacto(form: ContactoForm):
    print(f"Mensaje recibido de: {form.nombre}")
    if supabase:
        try:
            supabase.table("contactos").insert({
                "nombre": form.nombre,
                "correo": form.correo,
                "whatsapp": form.whatsapp,
                "proyecto": form.proyecto
            }).execute()
            return {"status": "success", "message": "Guardado en Supabase"}
        except Exception as e:
            return {"status": "error", "message": f"Error de BD: {e}"}
    return {"status": "success", "message": "Backend activo (Modo simulación local)"}

# Endpoints explícitos para asegurar la carga limpia de la App y sus motores
@app.get("/")
async def read_index():
    return FileResponse('index.html')

@app.get("/manifest.json")
async def read_manifest():
    return FileResponse('manifest.json')

@app.get("/sw.js")
async def read_sw():
    return FileResponse('sw.js')

# Montar la carpeta raíz para servir el resto de páginas, imágenes y el video local
app.mount("/", StaticFiles(directory="."), name="static")