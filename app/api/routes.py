from fastapi import APIRouter, HTTPException, Depends
from loguru import logger
from app.schemas.prompts import PromptInput
from app.services.gemini_service import generate_results_from_text, assess_text_parameters # Add assess_text_parameters
from app.core.security import get_current_active_user
from app.models.user import User

router = APIRouter()
