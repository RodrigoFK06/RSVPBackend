from fastapi import APIRouter, HTTPException, Depends, status
from loguru import logger

from app.schemas.quiz import QuizCreateInput, QuizOutput, QuizQuestion, QuizValidateInput, QuizValidateOutput, QuizQuestionFeedback
from app.models.session import ReadingSession
from app.models.user import User
from app.core.security import get_current_active_user
from app.services import quiz_service # Assuming __init__.py in services
from app.services.gemini_service import assess_text_parameters # Add this import
# from app.models.quiz_attempt import QuizAttempt # Import QuizAttempt if needed for type hint, though service returns it


router = APIRouter(prefix="/api/quiz", tags=["Quiz"])

@router.post("", response_model=QuizOutput, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    quiz_input: QuizCreateInput,
    current_user: User = Depends(get_current_active_user)
):
    text_to_use = ""
    session_id_for_quiz = None

    if quiz_input.session_id:
        session = await ReadingSession.get(quiz_input.session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ReadingSession not found")
        if not session.text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ReadingSession has no text content")
        # Ensure user has access to this session if needed (e.g. session.user_id == current_user.id)
        # For now, assuming any authenticated user can generate a quiz for any session ID if they know it.
        # Or, more strictly:
        if session.user_id != str(current_user.id):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have access to this session's quiz")

        text_to_use = session.text
        # session_to_use = session # Not strictly needed here as quiz_service re-fetches
        session_id_for_quiz = str(session.id)

    elif quiz_input.text:
        text_to_use = quiz_input.text

        # AI assessments for difficulty and ideal time for new session
        ai_params = await assess_text_parameters(text_to_use)

        temp_session = ReadingSession(
            text=text_to_use,
            user_id=str(current_user.id),
            ai_estimated_ideal_reading_time_seconds=ai_params.get("ideal_time_seconds"),
            ai_text_difficulty=ai_params.get("difficulty", "unknown")
        )
        temp_session.update_word_count() # Calculate and set word_count
        await temp_session.insert()
        # session_to_use = temp_session # Not strictly needed here
        session_id_for_quiz = str(temp_session.id)
        logger.info(f"Created temporary session {session_id_for_quiz} for quiz from raw text with AI params.")
    else:
        # This case should be prevented by Pydantic model validator in QuizCreateInput
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either text or session_id must be provided")

    if not text_to_use.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text content is empty")

    try:
        # The service function will save questions to the session if session_id_for_quiz is valid
        updated_session = await quiz_service.create_or_update_quiz_for_session(session_id_for_quiz, text_to_use, current_user)

        if updated_session.quiz_questions is None: # Should be [] if no questions
                logger.error(f"Quiz questions field is None after generation for session {session_id_for_quiz}")
                raise HTTPException(status_code=500, detail="Quiz generation failed to produce questions.")

        return QuizOutput(
            reading_session_id=session_id_for_quiz,
            questions=updated_session.quiz_questions
        )
    except FileNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id_for_quiz} not found after attempting quiz generation.")
    except Exception as e:
        logger.error(f"Error in create_quiz endpoint: {e}", exc_info=True)
        # The service might raise generic Exception, map it to HTTPException
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e) or "Failed to create quiz")


@router.post("/validate", response_model=QuizValidateOutput, status_code=status.HTTP_200_OK)
async def validate_quiz_answers(
    validation_input: QuizValidateInput,
    current_user: User = Depends(get_current_active_user)
):
    try:
        # Ensure the user taking the quiz is the one associated with the session, if that's a rule
        # For now, we allow validation if the session exists and user is authenticated.
        # Could add:
        # target_session = await ReadingSession.get(validation_input.reading_session_id)
        # if not target_session:
        #     raise HTTPException(status_code=404, detail="Reading session not found")
        # if target_session.user_id != str(current_user.id):
        #     raise HTTPException(status_code=403, detail="User not authorized to validate quiz for this session")


        quiz_attempt_doc = await quiz_service.validate_and_score_quiz_answers(
            reading_session_id=validation_input.reading_session_id,
            user_answers=validation_input.answers,
            user=current_user
        )

        # Convert QuizAttempt document to QuizValidateOutput Pydantic model
        return QuizValidateOutput(
            reading_session_id=quiz_attempt_doc.reading_session_id,
            overall_score=quiz_attempt_doc.overall_score,
            results=quiz_attempt_doc.results # results field is already List[QuizQuestionFeedback]
        )

    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ReadingSession not found for validation.")
    except ValueError as ve: # Catch specific errors like "No quiz questions"
        logger.warning(f"Validation error for session {validation_input.reading_session_id} by user {current_user.email}: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error validating quiz for session {validation_input.reading_session_id} by user {current_user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to validate quiz answers.")
