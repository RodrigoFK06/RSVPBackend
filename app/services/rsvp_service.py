import os
import json
import httpx
from loguru import logger
from app.schemas.rsvp import RsvpOutput
from app.models.rsvp_session import RsvpSession

GEMINI_RSVP_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

async def ask_gemini_for_rsvp(topic: str, user_id: str) -> RsvpOutput:
    if not user_id:
        raise ValueError("user_id is required to create RSVP session")
        
    prompt = (
        f"Escribe un texto informativo extenso pero claro sobre el siguiente tema, "
        f"dirigido a lectores entre 15-20 años. Usa lenguaje sencillo, 3 párrafos como máximo. Tema: {topic}"
    )

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{GEMINI_RSVP_URL}?key={os.getenv('GEMINI_API_KEY')}",
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            res.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error calling Gemini for RSVP: {e.response.status_code} - {e.response.text}"
        )
        raise Exception("Error communicating with AI service.")
    except httpx.RequestError as e:
        logger.error(f"Network error calling Gemini for RSVP: {e}")
        raise Exception("Network error communicating with AI service.")

    try:
        data = res.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
        logger.error(f"Malformed Gemini RSVP response: {e}. Response: {res.text}")
        raise Exception("Malformed response from AI service.")

    # Asegurar que el texto no esté vacío
    if not text or not text.strip():
        logger.error(f"Gemini returned empty text for topic: {topic}")
        raise Exception("AI service returned empty text content.")

    words = text.replace("\n", " ").split()
    words = [word for word in words if word.strip()]  # Filtrar palabras vacías

    session = RsvpSession(
        topic=topic, 
        text=text.strip(), 
        words=words, 
        user_id=user_id
    )
    
    # Actualizar word count antes de guardar
    session.update_word_count()
    await session.insert()

    logger.info(f"Created RSVP session {session.id} for user {user_id} with {len(words)} words")

    return RsvpOutput(
        id=str(session.id),
        text=session.text,
        words=session.words,
    )
