import pytest
from httpx import AsyncClient
from app.models.rsvp_session import RsvpSession
from app.schemas.quiz import QuizQuestion
from app.schemas.rsvp import RsvpOutput
from app.services import rsvp_service, quiz_service, gemini_service
from app.api import rsvp_routes, assistant_routes, quiz_routes

@pytest.fixture(autouse=True)
def mock_gemini(monkeypatch):
    async def fake_ask_gemini_for_rsvp(topic: str, user_id: str) -> RsvpOutput:
        if not user_id:
            raise ValueError("user_id is required")
        session = RsvpSession(topic=topic, text="Mock text", words=["Mock", "text"], user_id=user_id)
        await session.insert()
        return RsvpOutput(id=str(session.id), text=session.text, words=session.words)

    async def fake_generate_quiz_questions_from_text(text_content: str, num_questions: int = 5, num_mc_options: int = 4):
        return [
            QuizQuestion(
                id="q1",
                question_text="What is 2+2?",
                question_type="multiple_choice",
                options=["1", "2", "4", "5"],
                correct_answer="4",
                explanation="2+2=4"
            )
        ]

    async def fake_evaluate_open_ended(*args, **kwargs):
        return {"evaluation": "correct", "feedback": "Good"}

    async def fake_assess_text_parameters(text_content: str) -> dict:
        return {"ideal_time_seconds": 10, "difficulty": "easy"}

    async def fake_assistant_response(query: str, context: str) -> str:
        return "Mock assistant response"

    monkeypatch.setattr(rsvp_service, "ask_gemini_for_rsvp", fake_ask_gemini_for_rsvp)
    monkeypatch.setattr(rsvp_routes, "ask_gemini_for_rsvp", fake_ask_gemini_for_rsvp)

    monkeypatch.setattr(quiz_service, "generate_quiz_questions_from_text", fake_generate_quiz_questions_from_text)
    monkeypatch.setattr(quiz_service, "evaluate_open_ended_answer_with_gemini", fake_evaluate_open_ended)
    monkeypatch.setattr(quiz_routes, "assess_text_parameters", fake_assess_text_parameters)
    monkeypatch.setattr(gemini_service, "assess_text_parameters", fake_assess_text_parameters)
    monkeypatch.setattr(gemini_service, "get_contextual_assistant_response", fake_assistant_response)
    monkeypatch.setattr(assistant_routes, "get_contextual_assistant_response", fake_assistant_response)


def get_headers(token: dict) -> dict:
    return {"Authorization": token["Authorization"]}


@pytest.mark.asyncio
async def test_rsvp_generation(client: AsyncClient, authenticated_user_token: dict):
    headers = get_headers(authenticated_user_token)
    response = await client.post("/api/rsvp", json={"topic": "math"}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Mock text"
    assert await RsvpSession.get(data["id"]) is not None


@pytest.mark.asyncio
async def test_quiz_create_validate_and_stats(client: AsyncClient, authenticated_user_token: dict):
    headers = get_headers(authenticated_user_token)
    # create RSVP
    rsvp_resp = await client.post("/api/rsvp", json={"topic": "math"}, headers=headers)
    session_id = rsvp_resp.json()["id"]

    # create quiz
    quiz_resp = await client.post("/api/quiz", json={"rsvp_session_id": session_id}, headers=headers)
    assert quiz_resp.status_code == 201
    quiz_data = quiz_resp.json()
    assert quiz_data["rsvp_session_id"] == session_id
    assert len(quiz_data["questions"]) == 1

    # validate quiz
    validate_payload = {
        "rsvp_session_id": session_id,
        "answers": [{"question_id": "q1", "user_answer": "4"}],
        "reading_time_seconds": 12,
    }
    val_resp = await client.post("/api/quiz/validate", json=validate_payload, headers=headers)
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["overall_score"] == 100.0

    session_resp = await client.get(f"/api/rsvp/{session_id}", headers=headers)
    session_data = session_resp.json()
    assert session_data["quiz_taken"] is True
    assert session_data["quiz_score"] == 100.0
    assert session_data["reading_time_seconds"] == 12
    assert session_data["wpm"] == pytest.approx((len(session_data["words"]) / 12) * 60, abs=0.01)

    # stats
    stats_resp = await client.get("/api/stats", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "user_id" in stats
    assert "overall_stats" in stats


@pytest.mark.asyncio
async def test_assistant_endpoint(client: AsyncClient, authenticated_user_token: dict):
    headers = get_headers(authenticated_user_token)
    rsvp_resp = await client.post("/api/rsvp", json={"topic": "math"}, headers=headers)
    session_id = rsvp_resp.json()["id"]
    assistant_resp = await client.post(
        "/api/assistant",
        json={"query": "Explain", "rsvp_session_id": session_id},
        headers=headers,
    )
    assert assistant_resp.status_code == 200
    assert assistant_resp.json()["response"] == "Mock assistant response"


@pytest.mark.asyncio
async def test_delete_rsvp_session(client: AsyncClient, authenticated_user_token: dict):
    headers = get_headers(authenticated_user_token)

    rsvp_resp = await client.post("/api/rsvp", json={"topic": "history"}, headers=headers)
    session_id = rsvp_resp.json()["id"]

    stats_before = await client.get("/api/stats", headers=headers)
    assert session_id in [s["session_id"] for s in stats_before.json()["recent_sessions_stats"]]

    del_resp = await client.delete(f"/api/rsvp/{session_id}", headers=headers)
    assert del_resp.status_code == 204

    stats_after = await client.get("/api/stats", headers=headers)
    assert session_id not in [s["session_id"] for s in stats_after.json()["recent_sessions_stats"]]

    get_resp = await client.get(f"/api/rsvp/{session_id}", headers=headers)
    assert get_resp.status_code == 404
