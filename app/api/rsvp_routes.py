from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, status
from loguru import logger
from typing import List
from app.schemas.rsvp import RsvpInput, RsvpOutput
from app.services.rsvp_service import ask_gemini_for_rsvp
from app.models.rsvp_session import RsvpSession
from fastapi import Path
from app.core.security import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.post("/api/rsvp", response_model=RsvpOutput)
async def generate_rsvp(input_data: RsvpInput, current_user: User = Depends(get_current_active_user)):
    try:
        # Asegurar que el user_id se pase correctamente y no sea None
        user_id = str(current_user.id)
        logger.info(f"Generating RSVP for user {current_user.email} (ID: {user_id}) with topic: {input_data.topic}")
        
        return await ask_gemini_for_rsvp(input_data.topic, user_id=user_id)
    except ValueError as ve:
        logger.error(f"Validation error generating RSVP for user {current_user.email}: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(
            f"Error generating RSVP for user {current_user.email}: {e}", exc_info=True
        )
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/api/rsvp", response_model=List[RsvpOutput])
async def list_user_rsvp_sessions(
    current_user: User = Depends(get_current_active_user),
):
    """Listar todas las sesiones RSVP del usuario autenticado"""
    try:
        user_sessions = await RsvpSession.find(
            RsvpSession.user_id == str(current_user.id)
        ).sort(-RsvpSession.created_at).to_list()
        
        logger.info(f"Found {len(user_sessions)} sessions for user {current_user.email}")
        
        return [
            RsvpOutput(
                id=str(session.id),
                text=session.text,
                words=session.words,
            )
            for session in user_sessions
        ]
    except Exception as e:
        logger.error(f"Error fetching sessions for user {current_user.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching user sessions"
        )


@router.get("/api/rsvp/{session_id}", response_model=RsvpOutput)
async def get_rsvp_session(
    session_id: str = Path(..., description="ID de la sesión RSVP"),
    current_user: User = Depends(get_current_active_user),
):
    session = await RsvpSession.get(session_id)
    if not session or session.deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada")

    if session.user_id != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not own this session")

    return RsvpOutput(
        id=str(session.id),
        text=session.text,
        words=session.words,
        reading_time_seconds=session.reading_time_seconds,
        wpm=session.wpm,
        quiz_score=session.quiz_score,
        quiz_taken=session.quiz_taken,
    )


@router.delete("/api/rsvp/{session_id}", status_code=status.HTTP_200_OK)
async def delete_rsvp_session(
    session_id: str = Path(..., description="ID de la sesión RSVP"),
    current_user: User = Depends(get_current_active_user),
):
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="ID inválido")

    session = await RsvpSession.get(session_id)
    if not session or session.deleted:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    if session.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta sesión")

    session.deleted = True
    await session.save()

    return {"message": "Sesión eliminada correctamente"}
