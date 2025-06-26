from typing import List, Dict
from datetime import datetime, timedelta
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
            (session.reading_time_seconds or session.ai_estimated_ideal_reading_time_seconds or 0)
            for session in user_sessions
        )
        total_words_read = sum(session.word_count or 0 for session in user_sessions)

        average_wpm = None
        if total_reading_time_seconds > 0 and total_words_read > 0:
            average_wpm = round((total_words_read / total_reading_time_seconds) * 60, 2)

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

        # --- Compute Period Comparisons ---
        now = datetime.utcnow()
        current_start = now - timedelta(days=30)
        previous_start = now - timedelta(days=60)

        current_sessions = [
            s for s in user_sessions if s.created_at >= current_start
        ]
        previous_sessions = [
            s
            for s in user_sessions
            if previous_start <= s.created_at < current_start
        ]

        def period_metrics(sessions: List[RsvpSession]):
            reading_time = sum(
                (
                    s.reading_time_seconds
                    or s.ai_estimated_ideal_reading_time_seconds
                    or 0
                )
                for s in sessions
            )
            words = sum(s.word_count or 0 for s in sessions)
            wpm = None
            if reading_time > 0 and words > 0:
                wpm = round((words / reading_time) * 60, 2)
            scores: List[float] = []
            for s in sessions:
                sc = session_scores.get(str(s.id), [])
                if sc:
                    scores.append(max(sc))
                elif s.quiz_score is not None:
                    scores.append(s.quiz_score)
            comp = None
            if scores:
                comp = round(sum(scores) / len(scores), 2)
            return reading_time, words, wpm, comp

        (
            curr_reading_time,
            _curr_words,
            curr_wpm,
            curr_comp,
        ) = period_metrics(current_sessions)
        (
            prev_reading_time,
            _prev_words,
            prev_wpm,
            prev_comp,
        ) = period_metrics(previous_sessions)

        def calc_delta(curr: float | int | None, prev: float | int | None):
            if curr is None or prev is None or prev == 0:
                return None
            return round(((curr - prev) / prev) * 100, 2)

        delta_wpm = calc_delta(curr_wpm, prev_wpm)
        delta_comprehension = calc_delta(curr_comp, prev_comp)
        delta_reading_time = calc_delta(curr_reading_time, prev_reading_time)

        def trend(delta: float | None):
            if delta is None:
                return None
            if delta > 5:
                return "up"
            if delta < -5:
                return "down"
            return "stable"

        wpm_trend = trend(delta_wpm)
        comprehension_trend = trend(delta_comprehension)

        reading_progress_percent = None
        if len(user_sessions) >= 10:
            sorted_sessions = sorted(user_sessions, key=lambda s: s.created_at)

            def session_wpm(s: RsvpSession):
                if s.wpm is not None:
                    return s.wpm
                if s.reading_time_seconds and s.word_count:
                    return round((s.word_count / s.reading_time_seconds) * 60, 2)
                if (
                    s.ai_estimated_ideal_reading_time_seconds
                    and s.word_count
                ):
                    return round(
                        (s.word_count / s.ai_estimated_ideal_reading_time_seconds)
                        * 60,
                        2,
                    )
                return None

            first5 = sorted_sessions[:5]
            last5 = sorted_sessions[-5:]
            first_wpms = [session_wpm(s) for s in first5 if session_wpm(s) is not None]
            last_wpms = [session_wpm(s) for s in last5 if session_wpm(s) is not None]
            if first_wpms and last_wpms:
                first_avg = sum(first_wpms) / len(first_wpms)
                last_avg = sum(last_wpms) / len(last_wpms)
                if first_avg != 0:
                    reading_progress_percent = round(
                        ((last_avg - first_avg) / first_avg) * 100,
                        2,
                    )

        overall_stats = UserOverallStats(
            total_sessions_read=total_sessions_read,
            total_reading_time_seconds=total_reading_time_seconds,
            total_words_read=total_words_read,
            average_wpm=average_wpm,
            total_quizzes_taken=total_quizzes_taken,
            average_quiz_score=average_quiz_score,
            delta_wpm_vs_previous=delta_wpm,
            delta_comprehension_vs_previous=delta_comprehension,
            delta_reading_time_vs_previous=delta_reading_time,
            reading_progress_percent=reading_progress_percent,
            wpm_trend=wpm_trend,
            comprehension_trend=comprehension_trend,
        )

        # --- Prepare Recent Sessions Stats ---
        recent_sessions_stats: List[SessionStatDetail] = []
        for session in user_sessions[:recent_sessions_limit]:
            scores = session_scores.get(str(session.id), [])
            quiz_score = max(scores) if scores else None
            wpm = session.wpm
            if wpm is None and session.reading_time_seconds and session.word_count:
                wpm = round((session.word_count / session.reading_time_seconds) * 60, 2)
            elif wpm is None and session.ai_estimated_ideal_reading_time_seconds and session.word_count:
                wpm = round((session.word_count / session.ai_estimated_ideal_reading_time_seconds) * 60, 2)

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
                    reading_time_seconds=session.reading_time_seconds or session.ai_estimated_ideal_reading_time_seconds,
                    wpm=wpm,
                    quiz_taken=session.quiz_taken or bool(scores),
                    quiz_score=session.quiz_score if session.quiz_score is not None else quiz_score,
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
