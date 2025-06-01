from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.schemas.assistant import AssistantQueryInput, AssistantResponseOutput
from app.models.user import User
from app.models.session import ReadingSession # To fetch session text
from app.models.rsvp_session import RsvpSession # Added import
from app.core.security import get_current_active_user
from app.services.gemini_service import get_contextual_assistant_response

router = APIRouter(prefix="/api/assistant", tags=["AI Assistant"])

@router.post("", response_model=AssistantResponseOutput)
async def query_assistant(
    input_data: AssistantQueryInput,
    current_user: User = Depends(get_current_active_user)
):
    context_to_use = ""
    if input_data.rsvp_session_id:
        rsvp_session = await RsvpSession.get(input_data.rsvp_session_id)
        if not rsvp_session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RsvpSession not found")
        if rsvp_session.user_id != str(current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have access to this RSVP session's content")
        if not rsvp_session.text or not rsvp_session.text.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RsvpSession has no text content for context")
        context_to_use = rsvp_session.text

    elif input_data.session_id:
        session = await ReadingSession.get(input_data.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ReadingSession with id '{input_data.session_id}' not found."
            )
        if session.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to the specified session for contextual assistance."
            )
        if not session.text: # text in ReadingSession is non-optional, so this implies empty string check is enough
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ReadingSession '{input_data.session_id}' has no text content for context."
            )
        context_to_use = session.text

    elif input_data.text_context:
        context_to_use = input_data.text_context # Already validated by Pydantic

    else:
        # This case should be caught by Pydantic model validator
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Context (session_id or text_context) is required for the assistant."
        )

    try:
        ai_response = await get_contextual_assistant_response(input_data.query, context_to_use)
        return AssistantResponseOutput(response=ai_response)
    except Exception as e: # Catch any unexpected errors from the service
        logger.error(f"Error querying assistant for user {current_user.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request with the AI assistant."
        )
