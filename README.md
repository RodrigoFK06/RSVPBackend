# RIA – Lector Inteligente RSVP Backend

## Overview
RIA is a reading platform that applies the Rapid Serial Visual Presentation (RSVP) technique enhanced with AI. This FastAPI backend manages authentication, reading sessions, quizzes and statistics while delegating AI‑driven generation tasks to Google Gemini.

The service allows users to read a short text generated from a topic, interact with an assistant that uses the same text as context and answer an automatically built quiz to measure comprehension. All activity is stored in MongoDB so each user can review detailed statistics.

## Features
- **JWT authentication** – register, log in and retrieve your profile.
- **RSVP session generation** – create short texts with Gemini based on a topic.
- **Quiz creation and validation** – quizzes are built from the session text and user answers are evaluated.
- **Personal statistics** – see overall reading time, words read, quiz scores and details for recent sessions.
- **Contextual AI assistant** – ask questions about a session using the original text as context.

## Technology Stack
- [FastAPI](https://fastapi.tiangolo.com/) with Uvicorn
- [Beanie](https://github.com/roman-right/beanie) ODM and MongoDB
- Google Gemini API for text and quiz generation
- Authentication with `python-jose` and `passlib`
- Docker + Gunicorn for production deployment
- Pytest for automated tests

## Local Setup
1. Copy the sample environment file and edit it with your credentials:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies in a virtual environment:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```
   Visit `http://127.0.0.1:8000` to access the API.

`.env.example` provides these variables:
```env
MONGO_URL=mongodb://localhost:27017/rsvp_app
GEMINI_API_KEY=your-gemini-api-key
JWT_SECRET_KEY=your-jwt-secret-key
```

## Docker Usage
1. Build the image:
   ```bash
   docker build -t rsvp-backend .
   ```
2. Run the container with your environment variables:
   ```bash
   docker run -p 8000:8000 --env-file .env rsvp-backend
   ```

## API Reference
The API follows REST conventions. All endpoints except `/auth/register` and `/auth/login` require an `Authorization: Bearer <token>` header obtained from the login endpoint.

### Authentication
#### `POST /auth/register`
Create a new user.
```json
{
  "email": "user@example.com",
  "password": "strongpassword",
  "full_name": "John Doe"
}
```
Response:
```json
{
  "id": "<user-id>",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2025-01-01T12:00:00Z"
}
```

#### `POST /auth/login`
Obtain a JWT token.
```json
{
  "username": "user@example.com",
  "password": "strongpassword"
}
```
Response:
```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer"
}
```

#### `GET /auth/me`
Return the authenticated user's information.

### RSVP Sessions
#### `POST /api/rsvp`
Generate a new reading text based on the provided topic.
```json
{
  "topic": "quantum physics"
}
```
Response:
```json
{
  "id": "<session-id>",
  "text": "Generated text...",
  "words": ["Generated", "text..."]
}
```

#### `GET /api/rsvp/{session_id}`
Retrieve a previously generated session belonging to the current user.

### Quiz
#### `POST /api/quiz`
Create quiz questions for an RSVP session.
```json
{
  "rsvp_session_id": "<session-id>"
}
```
Response (truncated example):
```json
{
  "rsvp_session_id": "<session-id>",
  "questions": [
    {
      "id": "q1",
      "question_text": "What is 2+2?",
      "question_type": "multiple_choice",
      "options": ["1", "2", "4", "5"],
      "correct_answer": "4",
      "explanation": "2+2=4"
    }
  ]
}
```

#### `POST /api/quiz/validate`
Submit quiz answers for evaluation.
```json
{
  "rsvp_session_id": "<session-id>",
  "answers": [
    {
      "question_id": "q1",
      "user_answer": "4"
    }
  ]
}
```
Response:
```json
{
  "rsvp_session_id": "<session-id>",
  "overall_score": 100.0,
  "results": [
    {
      "question_id": "q1",
      "is_correct": true,
      "feedback": "Well done",
      "correct_answer": "4"
    }
  ]
}
```

### Statistics
#### `GET /api/stats`
Return aggregated statistics for the current user. Example response:
```json
{
  "user_id": "<user-id>",
  "overall_stats": {
    "total_sessions_read": 3,
    "total_reading_time_seconds": 180,
    "total_words_read": 900,
    "average_wpm": 300.0,
    "total_quizzes_taken": 3,
    "average_quiz_score": 90.0
  },
  "recent_sessions_stats": [
    {
      "session_id": "<session-id>",
      "text_snippet": "Lorem ipsum...",
      "word_count": 300,
      "reading_time_seconds": 60,
      "wpm": 300.0,
      "quiz_taken": true,
      "quiz_score": 100.0,
      "ai_text_difficulty": "easy",
      "ai_estimated_ideal_reading_time_seconds": 60,
      "created_at": "2025-01-01T12:00:00Z"
    }
  ],
  "personalized_feedback": null
}
```

### Assistant
#### `POST /api/assistant`
Ask a question about a session's text.
```json
{
  "query": "Explain the main idea",
  "rsvp_session_id": "<session-id>"
}
```
Response:
```json
{
  "response": "AI generated answer..."
}
```

## Example Usage with `curl`
```bash
# Register a new user
curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"strongpassword","full_name":"John"}'

# Login and store the token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
              -H "Content-Type: application/json" \
              -d '{"username":"user@example.com","password":"strongpassword"}' | jq -r .access_token)

# Generate a reading session
curl -X POST http://localhost:8000/api/rsvp \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"topic":"quantum physics"}'
```

## Running Tests
Install the requirements and execute:
```bash
pytest -q
```
The tests cover authentication flows, RSVP and quiz operations, and the assistant using mocked Gemini responses.

## Frontend
The accompanying frontend is built with Next.js and Zustand, offering a desktop-like reading interface. It communicates with this API for all operations.

## Contributing and License
Contributions are welcome via pull requests. This project is distributed under the MIT License.
