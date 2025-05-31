from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from app.models.session import ReadingSession
from app.schemas.prompts import PromptInput
from app.services.gemini_service import generate_results_from_text, assess_text_parameters # Add assess_text_parameters
from app.models.session import PromptResult
from app.core.security import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.post("/session", response_model=ReadingSession) # Ensure response_model is appropriate
async def create_session(data: PromptInput, current_user: User = Depends(get_current_active_user)):
    try:
        # AI assessments for difficulty and ideal time
        ai_params = await assess_text_parameters(data.text)

        # Generate summary, explanation etc.
        # Note: generate_results_from_text might be slow. Consider if it should be async task later.
        results = await generate_results_from_text(data.text)
        result_model = PromptResult(**results.model_dump())

        session = ReadingSession(
            text=data.text,
            user_id=str(current_user.id),
            results=result_model,
            # New fields
            ai_estimated_ideal_reading_time_seconds=ai_params.get("ideal_time_seconds"),
            ai_text_difficulty=ai_params.get("difficulty", "unknown")
            # reading_time_seconds will be updated by client later if feature is added
        )
        session.update_word_count() # Calculate and set word_count
        await session.insert()

        # The ReadingSession model itself is returned.
        # Ensure that Pydantic serialization handles ObjectId to str for session.id if not done by Beanie's response_model.
        # FastAPI does a good job with Beanie documents as response models.
        return session
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error creating session for user {current_user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing session")


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    session = await ReadingSession.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return session
