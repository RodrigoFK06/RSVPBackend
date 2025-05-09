from fastapi import APIRouter, HTTPException
from app.models.session import ReadingSession
from app.schemas.prompts import PromptInput
from app.services.gemini_service import generate_results_from_text
from app.models.session import PromptResult
router = APIRouter()

@router.post("/session")
async def create_session(data: PromptInput):
    try:
        results = await generate_results_from_text(data.text)
        result_model = PromptResult(**results.model_dump())  # 👈 conversión correcta
        session = ReadingSession(
            text=data.text,
            user_id=data.user_id,
            results=result_model
        )
        await session.insert()
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    session = await ReadingSession.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return session
