from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# 1. Definimos la estructura de los datos que envía tu HTML
class ContactoForm(BaseModel):
    nombre: str
    correo: str
    whatsapp: str = ""
    proyecto: str

# (Aquí asumo que ya tienes tu app = FastAPI() definida arriba en tu código)

# 2. Función interna que hace el envío real del correo
def enviar_alerta_correo(datos: ContactoForm):
    # Usamos variables de entorno por seguridad (para no poner tu clave pública en el código)
    remitente = os.environ.get("EMAIL_USER")      # info@quantrum1.com
    password = os.environ.get("EMAIL_PASS")       # Tu clave del correo
    servidor_smtp = os.environ.get("SMTP_SERVER") # Ej: mail.quantrum1.com
    puerto = int(os.environ.get("SMTP_PORT", 465))

    if not remitente or not password:
        print("Error: Faltan credenciales de correo en Render")
        return

    # Armamos el mensaje
    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = f"🔥 Nuevo Lead Quantrum: {datos.nombre}"
    mensaje["From"] = remitente
    mensaje["To"] = remitente # Te lo envías a ti mismo para que llegue a tu bandeja

    # El cuerpo del correo que tú leerás
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

    # Conexión al servidor de tu Reseller Hosting
    try:
        if puerto == 465:
            server = smtplib.SMTP_SSL(servidor_smtp, puerto)
        else:
            server = smtplib.SMTP(servidor_smtp, puerto)
            server.starttls()
            
        server.login(remitente, password)
        server.sendmail(remitente, remitente, mensaje.as_string())
        server.quit()
        print("Correo de alerta enviado con éxito.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

# 3. La ruta o "Endpoint" que recibe el llamado de tu página web
@app.post("/api/contacto")
async def procesar_contacto(datos: ContactoForm, background_tasks: BackgroundTasks):
    try:
        # Usamos background_tasks para que la web le responda "Éxito" al cliente de inmediato, 
        # mientras Python envía el correo silenciosamente en el fondo.
        background_tasks.add_task(enviar_alerta_correo, datos)
        return {"status": "success", "mensaje": "Mensaje recibido"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error procesando el formulario")