from typing import List, Optional, Dict
from loguru import logger
from datetime import timedelta # For time calculations if needed

from app.models.user import User
from app.models.quiz_attempt import QuizAttempt
from app.schemas.stats import UserStatsOutput, UserOverallStats, SessionStatDetail, PersonalizedFeedback
# Potentially an AI service for personalized feedback later
# from app.services.gemini_service import generate_personalized_stats_feedback

class StatsService:
    @staticmethod
    async def get_user_stats(user: User, recent_sessions_limit: int = 5) -> UserStatsOutput:
        user_id_str = str(user.id)
        logger.warning("ReadingSession model is missing. StatsService will return empty/default stats.")

        # Mocked/empty data since ReadingSession is unavailable
        user_sessions = [] # await ReadingSession.find(ReadingSession.user_id == user_id_str).sort(-ReadingSession.created_at).to_list()
        user_quiz_attempts = await QuizAttempt.find(QuizAttempt.user_id == user_id_str).to_list()

        # --- Calculate Overall Stats ---
        total_sessions_read = 0 # len(user_sessions)
        total_reading_time_seconds_actual = 0
        total_words_read = 0

        # for session in user_sessions:
        #     if session.reading_time_seconds: # Only sum if actual time is recorded
        #         total_reading_time_seconds_actual += session.reading_time_seconds
        #     if session.word_count:
        #         total_words_read += session.word_count

        average_wpm_actual = None
        # if total_reading_time_seconds_actual > 0 and total_words_read > 0:
        #     average_wpm_actual = round((total_words_read / total_words_read) * 60, 2) # Error: total_words_read / total_reading_time_seconds_actual

        total_quizzes_taken = 0
        total_quiz_score_sum = 0.0
        session_to_quiz_score_map: Dict[str, float] = {}
        attempted_session_ids = set()

        for attempt in user_quiz_attempts:
            # Assuming attempt.reading_session_id might be used elsewhere or for future linking
            # For now, we can't link it to a ReadingSession
            # session_to_quiz_score_map[attempt.reading_session_id] = attempt.overall_score
            # attempted_session_ids.add(attempt.reading_session_id)
            # To avoid breaking quiz stats completely, let's count attempts differently
            # This part needs careful review based on how QuizAttempt relates to sessions if ReadingSession is gone
            pass # Quiz stats might be inaccurate or need redesign without ReadingSession context

        # This logic needs re-evaluation. If sessions are gone, how are quizzes counted?
        # For now, let's base it on unique quiz attempts if they don't rely on session details for uniqueness beyond ID
        unique_quiz_session_ids_from_attempts = {attempt.reading_session_id for attempt in user_quiz_attempts if attempt.reading_session_id}
        total_quizzes_taken = len(unique_quiz_session_ids_from_attempts)
        for attempt in user_quiz_attempts:
            if attempt.reading_session_id in unique_quiz_session_ids_from_attempts:
                 total_quiz_score_sum += attempt.overall_score
                 # Avoid double counting if multiple attempts for the same session_id exist and we only want to count the session once
                 unique_quiz_session_ids_from_attempts.remove(attempt.reading_session_id)


        average_quiz_score = None
        if total_quizzes_taken > 0:
            # Need to ensure this doesn't divide by zero if logic changes
            # total_quiz_score_sum is summed per attempt, but total_quizzes_taken is per unique session_id in attempts.
            # This might be okay if one attempt per session_id is the norm, or if we sum latest scores.
            # For now, direct division.
            average_quiz_score = round(total_quiz_score_sum / total_quizzes_taken, 2)


        overall_stats = UserOverallStats(
            total_sessions_read=total_sessions_read,
            total_reading_time_seconds=total_reading_time_seconds_actual,
            total_words_read=total_words_read,
            average_wpm=average_wpm_actual,
            total_quizzes_taken=total_quizzes_taken, # This will use the count from QuizAttempts
            average_quiz_score=average_quiz_score # This will use scores from QuizAttempts
        )

        # --- Prepare Recent Sessions Stats ---
        recent_sessions_stats: List[SessionStatDetail] = []
        # for session in user_sessions[:recent_sessions_limit]:
        #     session_id_str_loop = str(session.id)
        #     quiz_score_for_session = session_to_quiz_score_map.get(session_id_str_loop)
        #     text_snippet = (session.text[:75] + "...") if session.text and len(session.text) > 75 else session.text
        #     recent_sessions_stats.append(SessionStatDetail(
        #         session_id=session_id_str_loop,
        #         text_snippet=text_snippet,
        #         word_count=session.word_count,
        #         reading_time_seconds=session.reading_time_seconds,
        #         wpm=session.calculated_wpm,
        #         quiz_taken=(quiz_score_for_session is not None),
        #         quiz_score=quiz_score_for_session,
        #         ai_text_difficulty=session.ai_text_difficulty,
        #         ai_estimated_ideal_reading_time_seconds=session.ai_estimated_ideal_reading_time_seconds,
        #         created_at=session.created_at
        #     ))

        personalized_feedback = None

        return UserStatsOutput(
            user_id=user_id_str,
            overall_stats=overall_stats,
            recent_sessions_stats=recent_sessions_stats, # Will be empty
            personalized_feedback=personalized_feedback
        )
