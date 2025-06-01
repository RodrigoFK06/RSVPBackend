import os
import httpx
import json
import uuid # For generating question IDs
from typing import List, Optional
from loguru import logger

from app.schemas.quiz import QuizQuestion, QuizOutput, QuizAnswerInput, QuizQuestionFeedback
from app.models.session import ReadingSession
from app.models.user import User # For type hinting if needed
from app.models.quiz_attempt import QuizAttempt # import QuizAttempt

# Assuming GEMINI_URL is defined, or use a specific one for quiz generation
# Re-using GEMINI_URL from gemini_service.py might be okay, or define a new one if needed.
# from app.services.gemini_service import GEMINI_URL # If we want to share the constant

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Fallback URL if not imported
GEMINI_QUIZ_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


async def generate_quiz_questions_from_text(text_content: str, num_questions: int = 5, num_mc_options: int = 4) -> List[QuizQuestion]:
    prompt = f"""
    Based on the following text, generate a list of {num_questions} quiz questions.
    Each question should be distinct and test different aspects of the text.
    Include a mix of multiple-choice and open-ended questions if possible, or specify if you want only one type.
    For each question, provide the following in JSON format:
    - "id": A unique UUID string for the question.
    - "question_text": The full text of the question.
    - "question_type": Either "multiple_choice" or "open_ended".
    - "options": For "multiple_choice" questions, a list of {num_mc_options} string options. For "open_ended", this can be null or an empty list.
    - "correct_answer": For "multiple_choice", the exact string of the correct option. For "open_ended", a concise model answer.
    - "explanation": (Optional) A brief explanation for why the answer is correct, especially for tricky questions.

    Output ONLY a valid JSON array of question objects, like this:
    [
        {{
            "id": "generated-uuid-1",
            "question_text": "What is the main topic of the text?",
            "question_type": "open_ended",
            "options": null,
            "correct_answer": "The main topic is...",
            "explanation": "This is clear from the introductory paragraph."
        }},
        {{
            "id": "generated-uuid-2",
            "question_text": "Which of these is a feature of X?",
            "question_type": "multiple_choice",
            "options": ["Option A", "Option B", "Correct Option C", "Option D"],
            "correct_answer": "Correct Option C",
            "explanation": "The text states that C is a primary feature."
        }}
    ]

    Text for quiz generation:
    ---
    {text_content}
    ---
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    quiz_questions: List[QuizQuestion] = []
    response_data_for_logging = None # Initialize for logging in case of early error

    try:
        async with httpx.AsyncClient(timeout=60.0) as client: # Increased timeout
            res = await client.post(
                f"{GEMINI_QUIZ_URL}?key={GEMINI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            res.raise_for_status() # Raise HTTPStatusError for bad responses (4xx or 5xx)

        response_data_for_logging = res.json() # Store for potential error logging
        # Extract the text content which should be the JSON string
        json_text_response = response_data_for_logging["candidates"][0]["content"]["parts"][0]["text"]

        # Clean the response to ensure it's valid JSON
        # Gemini might wrap JSON in ```json ... ``` or add other text.
        if "```json" in json_text_response:
            json_text_response = json_text_response.split("```json")[1].split("```")[0].strip()

        logger.info(f"Cleaned Gemini JSON response for quiz: {json_text_response}")
        raw_questions = json.loads(json_text_response)

        for i, q_data in enumerate(raw_questions):
            # Ensure ID is present, generate if missing (though prompt asks for it)
            q_id = q_data.get("id", str(uuid.uuid4()))
            # Basic validation, Pydantic will do more
            if not all(k in q_data for k in ["question_text", "question_type", "correct_answer"]):
                logger.warning(f"Skipping question due to missing fields: {q_data}")
                continue

            # Ensure options are a list if multiple choice, even if Gemini forgets
            if q_data["question_type"] == "multiple_choice" and not isinstance(q_data.get("options"), list):
                q_data["options"] = [] # Or handle as error

            quiz_questions.append(QuizQuestion(**q_data, id=q_id)) # Pass id explicitly
            if len(quiz_questions) >= num_questions: # Stop if we have enough
                break

        # If not enough questions generated, log it
        if len(quiz_questions) < num_questions:
            logger.warning(f"Gemini generated {len(quiz_questions)} questions, expected {num_questions}.")

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling Gemini for quiz: {e.response.status_code} - {e.response.text}")
        raise Exception("Error communicating with AI for quiz generation.")
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
        logger.error(f"Error parsing Gemini response for quiz: {e}. Response: {json_text_response if 'json_text_response' in locals() else response_data_for_logging}")
        raise Exception("Error processing AI response for quiz generation.")
    except Exception as e:
        logger.error(f"Unexpected error in quiz generation: {e}")
        raise Exception("An unexpected error occurred while generating the quiz.")

    return quiz_questions

async def create_or_update_quiz_for_session(session_id: str, text_content: str, user: User) -> ReadingSession:
    session = await ReadingSession.get(session_id)
    if not session:
        raise FileNotFoundError("ReadingSession not found") # Or HTTPException

    # For now, always generate new questions. Could add logic to check if quiz_questions already exist.
    questions = await generate_quiz_questions_from_text(text_content)

    if not questions:
            # Fallback or error if no questions could be generated
        logger.warning(f"No quiz questions generated for session {session_id}")
        session.quiz_questions = [] # Ensure it's an empty list not None
    else:
        session.quiz_questions = questions

    await session.save()
    return session


async def evaluate_open_ended_answer_with_gemini(question_text: str, correct_answer_criteria: str, user_answer: str) -> dict:
    prompt = f"""
    Evaluate the user's answer to an open-ended question.
    Original Question: "{question_text}"
    Criteria for a correct answer / Model Answer: "{correct_answer_criteria}"
    User's Answer: "{user_answer}"

    Is the user's answer correct, partially correct, or incorrect based on the criteria/model answer?
    Provide brief feedback for the user, explaining your evaluation.

    Return your evaluation as a JSON object with two keys:
    - "evaluation": A string, one of "correct", "partially_correct", or "incorrect".
    - "feedback": A string, your feedback to the user.

    Example JSON output:
    {{
        "evaluation": "partially_correct",
        "feedback": "Your answer mentions some key points but misses the main aspect of X."
    }}
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    evaluation_result = {"evaluation": "error", "feedback": "Could not evaluate answer."}
    response_data_for_logging = None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client: # Shorter timeout for evaluation
            res = await client.post(
                f"{GEMINI_QUIZ_URL}?key={GEMINI_API_KEY}", # Using the same GEMINI_QUIZ_URL
                headers={"Content-Type": "application/json"},
                json=payload
            )
            res.raise_for_status()

        response_data_for_logging = res.json()
        json_text_response = response_data_for_logging["candidates"][0]["content"]["parts"][0]["text"]

        if "```json" in json_text_response: # Clean if necessary
            json_text_response = json_text_response.split("```json")[1].split("```")[0].strip()

        logger.info(f"Gemini evaluation response: {json_text_response}")
        evaluation_data = json.loads(json_text_response)

        # Basic validation of Gemini's output
        if "evaluation" in evaluation_data and "feedback" in evaluation_data:
            evaluation_result = evaluation_data
        else:
            logger.warning(f"Gemini evaluation output missing keys: {evaluation_data}")
            evaluation_result['feedback'] = "AI evaluation response was not in the expected format."

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling Gemini for open-ended evaluation: {e.response.status_code} - {e.response.text}")
        evaluation_result['feedback'] = "Error communicating with AI for answer evaluation."
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"Error parsing Gemini response for open-ended evaluation: {e}. Response: {json_text_response if 'json_text_response' in locals() else response_data_for_logging}")
        evaluation_result['feedback'] = "Error processing AI response for answer evaluation."
    except Exception as e:
        logger.error(f"Unexpected error in open-ended evaluation: {e}")
        evaluation_result['feedback'] = "An unexpected error occurred during answer evaluation."

    return evaluation_result


async def validate_and_score_quiz_answers(
    reading_session_id: str,
    user_answers: List[QuizAnswerInput],
    user: User
) -> QuizAttempt:
    session = await ReadingSession.get(reading_session_id)
    if not session:
        raise FileNotFoundError("ReadingSession not found")
    if not session.quiz_questions:
        raise ValueError("No quiz questions found for this session")

    feedback_results: List[QuizQuestionFeedback] = []
    correct_answers_count = 0

    questions_map = {q.id: q for q in session.quiz_questions}

    for answer_input in user_answers:
        question = questions_map.get(answer_input.question_id)
        if not question:
            logger.warning(f"Question ID {answer_input.question_id} not found in session {reading_session_id}. Skipping.")
            feedback_results.append(QuizQuestionFeedback(
                question_id=answer_input.question_id,
                is_correct=False,
                feedback="Question not found for this attempt.",
                correct_answer="N/A"
            ))
            continue

        is_correct = False
        feedback_text = ""

        if question.question_type == "multiple_choice":
            is_correct = (answer_input.user_answer == question.correct_answer)
            feedback_text = "Correct!" if is_correct else "Incorrect."
            if question.explanation:
                feedback_text += f" {question.explanation}"

        elif question.question_type == "open_ended":
            # Use Gemini for evaluation
            evaluation = await evaluate_open_ended_answer_with_gemini(
                question.question_text,
                question.correct_answer, # Model answer/criteria
                answer_input.user_answer
            )
            # Define what constitutes "correct" from Gemini's evaluation
            is_correct = evaluation["evaluation"] in ["correct", "partially_correct"]
            feedback_text = evaluation["feedback"]

        else: # Should not happen if data is clean
            feedback_text = "Unknown question type."

        if is_correct:
            correct_answers_count += 1

        feedback_results.append(QuizQuestionFeedback(
            question_id=question.id,
            is_correct=is_correct,
            feedback=feedback_text,
            correct_answer=question.correct_answer
        ))

    overall_score = (correct_answers_count / len(session.quiz_questions)) * 100 if session.quiz_questions else 0

    quiz_attempt = QuizAttempt(
        reading_session_id=str(session.id), # Ensure it's str
        user_id=str(user.id), # Ensure it's str
        results=feedback_results,
        overall_score=round(overall_score, 2)
    )
    await quiz_attempt.insert()

    return quiz_attempt
