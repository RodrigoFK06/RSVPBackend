from typing import List, Dict
from loguru import logger

from app.models.user import User
from app.models.quiz_attempt import QuizAttempt
from app.models.rsvp_session import RsvpSession
from app.schemas.stats import (
    UserStatsOutput,
    UserOverallStats,
    SessionStatDetail,
    PersonalizedFeedback,
)
from app.utils.timezone import convert_utc_to_local
# Potentially an AI service for personalized feedback later
# from app.services.gemini_service import generate_personalized_stats_feedback

class StatsService:
    @staticmethod
    async def get_user_stats(user: User, recent_sessions_limit: int = 5) -> UserStatsOutput:
        user_id_str = str(user.id)

        # Fetch user's sessions and quiz attempts
        user_sessions = (
            await RsvpSession.find(
                RsvpSession.user_id == user_id_str,
                RsvpSession.deleted == False,
            )
            .sort(-RsvpSession.created_at)
            .to_list()
        )
        user_quiz_attempts = await QuizAttempt.find(
            QuizAttempt.user_id == user_id_str
        ).to_list()

        # --- Calculate Overall Session Stats ---
        total_sessions_read = len(user_sessions)
        total_reading_time_seconds = sum(
            session.ai_estimated_ideal_reading_time_seconds or 0
            for session in user_sessions
        )
        total_words_read = sum(session.word_count or 0 for session in user_sessions)

        average_wpm = None
        if total_reading_time_seconds > 0 and total_words_read > 0:
            average_wpm = round(
                (total_words_read / total_reading_time_seconds) * 60, 2
            )

        # --- Aggregate Quiz Attempts ---
        session_scores: Dict[str, List[float]] = {}
        for attempt in user_quiz_attempts:
            session_scores.setdefault(attempt.rsvp_session_id, []).append(
                attempt.overall_score
            )

        total_quizzes_taken = len(session_scores)
        average_quiz_score = None
        if total_quizzes_taken > 0:
            best_scores = [max(scores) for scores in session_scores.values()]
            average_quiz_score = round(sum(best_scores) / total_quizzes_taken, 2)

        overall_stats = UserOverallStats(
            total_sessions_read=total_sessions_read,
            total_reading_time_seconds=total_reading_time_seconds,
            total_words_read=total_words_read,
            average_wpm=average_wpm,
            total_quizzes_taken=total_quizzes_taken,
            average_quiz_score=average_quiz_score,
        )

        # --- Prepare Recent Sessions Stats ---
        recent_sessions_stats: List[SessionStatDetail] = []
        for session in user_sessions[:recent_sessions_limit]:
            scores = session_scores.get(str(session.id), [])
            quiz_score = max(scores) if scores else None
            wpm = None
            if (
                session.ai_estimated_ideal_reading_time_seconds
                and session.word_count
            ):
                wpm = round(
                    (session.word_count
                    / session.ai_estimated_ideal_reading_time_seconds)
                    * 60,
                    2,
                )

            text_snippet = (
                session.text[:75] + "..."
                if session.text and len(session.text) > 75
                else session.text
            )

            recent_sessions_stats.append(
                SessionStatDetail(
                    session_id=str(session.id),
                    text_snippet=text_snippet,
                    word_count=session.word_count,
                    reading_time_seconds=session.ai_estimated_ideal_reading_time_seconds,
                    wpm=wpm,
                    quiz_taken=bool(scores),
                    quiz_score=quiz_score,
                    ai_text_difficulty=session.ai_text_difficulty,
                    ai_estimated_ideal_reading_time_seconds=session.ai_estimated_ideal_reading_time_seconds,
                    created_at=session.created_at,
                    created_at_local=convert_utc_to_local(session.created_at),
                )
            )

        personalized_feedback = None

        return UserStatsOutput(
            user_id=user_id_str,
            overall_stats=overall_stats,
            recent_sessions_stats=recent_sessions_stats,
            personalized_feedback=personalized_feedback,
        )
