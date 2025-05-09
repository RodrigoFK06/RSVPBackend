from fastapi import APIRouter, HTTPException
from app.schemas.rsvp import RsvpInput, RsvpOutput
from app.services.rsvp_service import ask_gemini_for_rsvp
from app.models.rsvp_session import RsvpSession
from fastapi import Path
router = APIRouter()

@router.post("/api/rsvp", response_model=RsvpOutput)
async def generate_rsvp(input: RsvpInput):
    try:
        return await ask_gemini_for_rsvp(input.topic, user_id=input.user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/rsvp/{session_id}", response_model=RsvpOutput)
async def get_rsvp_session(session_id: str = Path(..., description="ID de la sesión RSVP")):
    session = await RsvpSession.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    return RsvpOutput(
        id=str(session.id),
        text=session.text,
        words=session.words
    )