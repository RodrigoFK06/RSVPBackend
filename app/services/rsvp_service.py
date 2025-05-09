import os
import httpx
from app.schemas.rsvp import RsvpOutput
from app.models.rsvp_session import RsvpSession

GEMINI_RSVP_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

async def ask_gemini_for_rsvp(topic: str, user_id: str = None) -> RsvpOutput:
    prompt = f"Escribe un texto informativo extenso pero claro sobre el siguiente tema, dirigido a lectores entre 15-20 años. Usa lenguaje sencillo, 3 párrafos como máximo. Tema: {topic}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{GEMINI_RSVP_URL}?key={os.getenv('GEMINI_API_KEY')}",
            headers={"Content-Type": "application/json"},
            json=payload
        )

        data = res.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        words = text.replace("\n", " ").split()

        # Guardar en Mongo
        session = RsvpSession(topic=topic, text=text.strip(), words=words, user_id=user_id)
        await session.insert()

        return RsvpOutput(
            id=str(session.id),  # 👈 convertimos ObjectId a str
            text=session.text,
            words=session.words
        )
