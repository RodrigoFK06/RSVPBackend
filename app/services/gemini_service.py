import os
import httpx
from app.schemas.prompts import PromptOutput

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

async def ask_gemini(prompt: str) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{GEMINI_URL}?key={os.getenv('GEMINI_API_KEY')}",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        data = res.json()
        print("RESPUESTA COMPLETA DE GEMINI:\n", data)
        return data["candidates"][0]["content"]["parts"][0]["text"]

async def generate_results_from_text(text: str) -> PromptOutput:
    summary = await ask_gemini(f"Resume este texto:\n{text}")
    explanation = await ask_gemini(f"Explica este texto detalladamente:\n{text}")
    questions = await ask_gemini(f"Genera 5 preguntas tipo test con 4 alternativas cada una basadas en este texto:\n{text}")
    glossary = await ask_gemini(f"Extrae 5 palabras difíciles de este texto y explica su significado:\n{text}")

    return PromptOutput(
        summary=summary.strip(),
        explanation=explanation.strip(),
        questions=[q.strip() for q in questions.split("\n") if q.strip()],
        glossary={str(i+1): item.strip() for i, item in enumerate(glossary.split("\n")) if item.strip()}
    )
