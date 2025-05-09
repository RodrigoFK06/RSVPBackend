from fastapi import FastAPI
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import sys

from app.models.session import ReadingSession
from app.models.rsvp_session import RsvpSession
from app.api.routes import router
from app.api import rsvp_routes

# Cargar variables del archivo .env
load_dotenv()

# Verificar y mostrar claves críticas
mongo_url = os.getenv("MONGO_URL")
gemini_key = os.getenv("GEMINI_API_KEY")

if not mongo_url:
    print("❌ ERROR: MONGO_URL no está definido en el archivo .env", file=sys.stderr)
    sys.exit(1)

if not gemini_key:
    print("❌ ERROR: GEMINI_API_KEY no está definido en el archivo .env", file=sys.stderr)
    sys.exit(1)

print("✅ MONGO_URL y GEMINI_API_KEY cargados correctamente")

# Crear instancia de la app
app = FastAPI()

# Inicializar MongoDB con Beanie
@app.on_event("startup")
async def app_init():
    client = AsyncIOMotorClient(mongo_url)
    await init_beanie(database=client["rsvp_app"], document_models=[ReadingSession, RsvpSession])

# Registrar rutas de la API (ambas)
app.include_router(router)
app.include_router(rsvp_routes.router)
