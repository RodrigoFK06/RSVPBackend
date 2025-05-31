from typing import List, Optional, Dict
from loguru import logger
from datetime import timedelta # For time calculations if needed

from app.models.user import User
from app.models.session import ReadingSession
from app.models.quiz_attempt import QuizAttempt
from app.schemas.stats import UserStatsOutput, UserOverallStats, SessionStatDetail, PersonalizedFeedback
# Potentially an AI service for personalized feedback later
# from app.services.gemini_service import generate_personalized_stats_feedback

class StatsService:
    @staticmethod
    async def get_user_stats(user: User, recent_sessions_limit: int = 5) -> UserStatsOutput:
        user_id_str = str(user.id)

        # Fetch all sessions and attempts for the user
        # For performance on many records, consider projections to fetch only needed fields
        user_sessions = await ReadingSession.find(ReadingSession.user_id == user_id_str).sort(-ReadingSession.created_at).to_list()
        user_quiz_attempts = await QuizAttempt.find(QuizAttempt.user_id == user_id_str).to_list()

        # --- Calculate Overall Stats ---
        total_sessions_read = len(user_sessions)
        total_reading_time_seconds_actual = 0
        total_words_read = 0

        for session in user_sessions:
            if session.reading_time_seconds: # Only sum if actual time is recorded
                total_reading_time_seconds_actual += session.reading_time_seconds
            if session.word_count:
                total_words_read += session.word_count

        average_wpm_actual = None
        if total_reading_time_seconds_actual > 0 and total_words_read > 0:
            average_wpm_actual = round((total_words_read / total_reading_time_seconds_actual) * 60, 2)

        total_quizzes_taken = 0
        total_quiz_score_sum = 0.0 # Ensure float for sum
        # Create a map of session IDs to quiz scores for efficient lookup
        session_to_quiz_score_map: Dict[str, float] = {}
        # Ensure we count unique quizzes taken, e.g., based on distinct reading_session_id in attempts
        attempted_session_ids = set()

        for attempt in user_quiz_attempts:
            session_to_quiz_score_map[attempt.reading_session_id] = attempt.overall_score
            attempted_session_ids.add(attempt.reading_session_id)

        total_quizzes_taken = len(attempted_session_ids)
        # Sum scores for sessions where a quiz was actually recorded in QuizAttempt
        for session_id_with_quiz in attempted_session_ids:
            if session_id_with_quiz in session_to_quiz_score_map:
                total_quiz_score_sum += session_to_quiz_score_map[session_id_with_quiz]


        average_quiz_score = None
        if total_quizzes_taken > 0:
            average_quiz_score = round(total_quiz_score_sum / total_quizzes_taken, 2)

        overall_stats = UserOverallStats(
            total_sessions_read=total_sessions_read,
            total_reading_time_seconds=total_reading_time_seconds_actual,
            total_words_read=total_words_read,
            average_wpm=average_wpm_actual,
            total_quizzes_taken=total_quizzes_taken,
            average_quiz_score=average_quiz_score
        )

        # --- Prepare Recent Sessions Stats ---
        recent_sessions_stats: List[SessionStatDetail] = []
        for session in user_sessions[:recent_sessions_limit]:
            session_id_str_loop = str(session.id) # Use a different variable name
            quiz_score_for_session = session_to_quiz_score_map.get(session_id_str_loop)

            # Prepare a snippet of the text
            text_snippet = (session.text[:75] + "...") if session.text and len(session.text) > 75 else session.text

            recent_sessions_stats.append(SessionStatDetail(
                session_id=session_id_str_loop,
                text_snippet=text_snippet,
                word_count=session.word_count,
                reading_time_seconds=session.reading_time_seconds,
                wpm=session.calculated_wpm, # Use the property from ReadingSession model
                quiz_taken=(quiz_score_for_session is not None),
                quiz_score=quiz_score_for_session,
                ai_text_difficulty=session.ai_text_difficulty,
                ai_estimated_ideal_reading_time_seconds=session.ai_estimated_ideal_reading_time_seconds,
                created_at=session.created_at
            ))

        # --- Personalized Feedback (Placeholder for now) ---
        # personalized_feedback_text = await generate_personalized_stats_feedback(overall_stats.model_dump())
        # personalized_feedback = PersonalizedFeedback(feedback_text=personalized_feedback_text) if personalized_feedback_text else None
        personalized_feedback = None # Placeholder

        return UserStatsOutput(
            user_id=user_id_str,
            overall_stats=overall_stats,
            recent_sessions_stats=recent_sessions_stats,
            personalized_feedback=personalized_feedback
        )
