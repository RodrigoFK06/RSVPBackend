from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
import sys
from dotenv import load_dotenv
import os

from app.db.connection import connect_to_mongo

#from app.models.session import ReadingSession
from app.api.routes import router
from app.api import rsvp_routes, auth_routes, quiz_routes, stats_routes, assistant_routes

# Cargar variables del archivo .env
load_dotenv()

# Configure Loguru
logger.remove()  # Remove default handler
logger.add(sys.stderr, level="INFO") # Log to stderr with INFO level
logger.add("logs/error_{time}.log", level="ERROR", rotation="1 week") # Log errors to a file

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

# Exception handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception for {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException for {request.method} {request.url}: {exc.status_code} {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Inicializar MongoDB con Beanie
@app.on_event("startup")
async def app_init():
    await connect_to_mongo()

# Registrar rutas de la API (ambas)
app.include_router(router)
app.include_router(rsvp_routes.router)
app.include_router(auth_routes.router)
app.include_router(quiz_routes.router)
app.include_router(stats_routes.router)
app.include_router(assistant_routes.router)
