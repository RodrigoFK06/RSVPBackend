# RIA – Lector Inteligente RSVP Backend

This repository contains the FastAPI backend powering the "RIA – Lector Inteligente RSVP" application. The API allows users to generate reading sessions with the Rapid Serial Visual Presentation (RSVP) technique, obtain AI‑generated quizzes and explanations, and track personal reading statistics.

## Features
- **User authentication** with JWT tokens.
- **RSVP session generation** via Google's Gemini API.
- **Quiz creation and validation** for each session.
- **Contextual AI assistant** to answer questions about a text.
- **User statistics** summarising reading activity and quiz performance.

## Technologies
- FastAPI &amp; Uvicorn
- MongoDB with Beanie ODM
- Google Gemini API
- JWT authentication (`python-jose`, `passlib`)
- Docker + Gunicorn for production
- Pytest for automated tests

## Local Installation
1. Copy `.env.example` to `.env` and fill in your values:
   ```bash
   cp .env.example .env
   ```
2. Install the requirements (preferably in a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```
3. Start the application:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://127.0.0.1:8000`.

## Docker Usage
1. Build the image:
   ```bash
   docker build -t rsvp-backend .
   ```
2. Run the container using your `.env` file:
   ```bash
   docker run -p 8000:8000 --env-file .env rsvp-backend
   ```

## API Endpoints
| Method &amp; Path               | Description                                  |
|-------------------------------|----------------------------------------------|
| **POST /auth/register**       | Create a new user account                    |
| **POST /auth/login**          | Obtain a JWT access token                    |
| **GET  /auth/me**             | Retrieve the authenticated user              |
| **POST /api/rsvp**            | Generate a new RSVP reading session          |
| **GET  /api/rsvp/{id}**       | Fetch a previously generated session         |
| **POST /api/quiz**            | Create quiz questions for a session          |
| **POST /api/quiz/validate**   | Validate quiz answers and get feedback       |
| **GET  /api/stats**           | Retrieve statistics for the current user     |
| **POST /api/assistant**       | Ask context-aware questions about a session  |

All endpoints except registration and login require the `Authorization: Bearer <token>` header.

## Running Tests
After installing the dependencies, execute:
```bash
pytest
```
Mocked services are used so tests do not contact external APIs or MongoDB instances.

## Frontend
The companion front‑end (not included here) is built with Next.js and Zustand to provide a desktop‑like experience when reading and interacting with RSVP sessions.

