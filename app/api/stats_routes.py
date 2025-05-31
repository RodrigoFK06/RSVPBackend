from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.schemas.stats import UserStatsOutput
from app.models.user import User
from app.core.security import get_current_active_user
from app.services.stats_service import StatsService # Assuming StatsService is in this path

router = APIRouter(prefix="/api/stats", tags=["Statistics"])

@router.get("", response_model=UserStatsOutput)
async def get_user_statistics(
    current_user: User = Depends(get_current_active_user)
):
    try:
        user_stats = await StatsService.get_user_stats(user=current_user)
        return user_stats
    except Exception as e:
        logger.error(f"Error fetching stats for user {current_user.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching user statistics."
        )
