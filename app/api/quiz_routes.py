from fastapi import APIRouter, HTTPException, Depends, status
from loguru import logger

from app.schemas.quiz import QuizCreateInput, QuizOutput, QuizQuestion, QuizValidateInput, QuizValidateOutput, QuizQuestionFeedback
from app.models.user import User
from app.models.rsvp_session import RsvpSession
from app.core.security import get_current_active_user
from app.services import quiz_service
from app.services.gemini_service import assess_text_parameters

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])

@router.post("", response_model=QuizOutput, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    quiz_input: QuizCreateInput,
    current_user: User = Depends(get_current_active_user)
):
    rsvp_session = await RsvpSession.get(quiz_input.rsvp_session_id)
    if not rsvp_session or rsvp_session.deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RsvpSession not found")
    if rsvp_session.user_id != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have access to this RSVP session's content")
    if not rsvp_session.text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RsvpSession has no text content to create a quiz from.")

    try:
        # Generate quiz questions and add them to the session
        updated_rsvp_session = await quiz_service.create_or_update_quiz_for_session(
            rsvp_session_id=str(rsvp_session.id),
            text_content=rsvp_session.text,
            user=current_user
        )

        # Update AI analysis fields on the RsvpSession
        ai_params = await assess_text_parameters(updated_rsvp_session.text)
        updated_rsvp_session.ai_estimated_ideal_reading_time_seconds = ai_params.get("ideal_time_seconds")
        updated_rsvp_session.ai_text_difficulty = ai_params.get("difficulty", "unknown")
        updated_rsvp_session.update_word_count()
        await updated_rsvp_session.save()

        if updated_rsvp_session.quiz_questions is None:
            logger.error(f"Quiz questions field is None after generation for RsvpSession {updated_rsvp_session.id}")
            raise HTTPException(status_code=500, detail="Quiz generation failed to produce questions.")

        return QuizOutput(
            rsvp_session_id=str(updated_rsvp_session.id),
            questions=updated_rsvp_session.quiz_questions
        )
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"RsvpSession {quiz_input.rsvp_session_id} not found during quiz processing.")
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have access to this RSVP session")
    except Exception as e:
        logger.error(f"Error in create_quiz for RsvpSession {quiz_input.rsvp_session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e) or "Failed to create quiz")


@router.post("/validate", response_model=QuizValidateOutput, status_code=status.HTTP_200_OK)
async def validate_quiz_answers(
    validation_input: QuizValidateInput,
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Validar que el usuario tenga acceso a la sesión RSVP
        target_session = await RsvpSession.get(validation_input.rsvp_session_id)
        if not target_session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RsvpSession not found")
        if target_session.user_id != str(current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not authorized to validate quiz for this RsvpSession")

        logger.info(f"User {current_user.email} validating quiz for session {validation_input.rsvp_session_id}")

        quiz_attempt_doc = await quiz_service.validate_and_score_quiz_answers(
            rsvp_session_id=validation_input.rsvp_session_id,
            user_answers=validation_input.answers,
            user=current_user,
            reading_time_seconds=validation_input.reading_time_seconds,
        )

        # Convert QuizAttempt document to QuizValidateOutput Pydantic model
        return QuizValidateOutput(
            rsvp_session_id=quiz_attempt_doc.rsvp_session_id,
            overall_score=quiz_attempt_doc.overall_score,
            results=quiz_attempt_doc.results
        )

    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RsvpSession not found for validation.")
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have access to this RSVP session")
    except ValueError as ve:
        logger.warning(f"Validation error for RsvpSession {validation_input.rsvp_session_id} by user {current_user.email}: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error validating quiz for RsvpSession {validation_input.rsvp_session_id} by user {current_user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to validate quiz answers.")
