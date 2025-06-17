from fastapi import APIRouter, HTTPException, Depends, status
from loguru import logger
from app.schemas.rsvp import RsvpInput, RsvpOutput
from app.services.rsvp_service import ask_gemini_for_rsvp
from app.models.rsvp_session import RsvpSession
from fastapi import Path
from app.core.security import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.post("/api/rsvp", response_model=RsvpOutput)
async def generate_rsvp(input_data: RsvpInput, current_user: User = Depends(get_current_active_user)): # Renamed 'input' to 'input_data'
    try:
        # The ask_gemini_for_rsvp service will handle saving the user_id
        return await ask_gemini_for_rsvp(input_data.topic, user_id=str(current_user.id))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(
            f"Error generating RSVP for user {current_user.email}: {e}", exc_info=True
        )
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/api/rsvp/{session_id}", response_model=RsvpOutput)
async def get_rsvp_session(
    session_id: str = Path(..., description="ID de la sesión RSVP"),
    current_user: User = Depends(get_current_active_user),
):
    session = await RsvpSession.get(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada")

    if session.user_id != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not own this session")

    return RsvpOutput(
        id=str(session.id),
        text=session.text,
        words=session.words,
    )
