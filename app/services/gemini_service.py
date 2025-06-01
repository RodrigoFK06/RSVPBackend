import os
import httpx
import json # Added
from loguru import logger # Added
from app.schemas.prompts import PromptOutput

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

async def ask_gemini(prompt: str, model_url: str = GEMINI_URL) -> str: # Added model_url parameter
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY not found in ask_gemini.")
        raise ValueError("API key for Gemini not configured.")

    async with httpx.AsyncClient(timeout=60.0) as client: # General timeout for ask_gemini
        res = await client.post(
            f"{model_url}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        res.raise_for_status() # Raise HTTPStatusError for bad responses
        data = res.json()
        # Log the full response for debugging if needed, then extract text
        # logger.debug(f"Full Gemini response from ask_gemini: {data}")
        return data["candidates"][0]["content"]["parts"][0]["text"]

async def generate_results_from_text(text: str) -> PromptOutput:
    # Using GEMINI_PRO_URL for potentially more complex generation tasks if needed, or stick to GEMINI_URL
    # For now, using the default GEMINI_URL as passed by ask_gemini's default
    summary_prompt = f"Resume este texto:\n{text}"
    explanation_prompt = f"Explica este texto detalladamente:\n{text}"
    questions_prompt = f"Genera exactamente 5 preguntas tipo test con 4 alternativas cada una (A, B, C, D) basadas en este texto. Numera las preguntas del 1 al 5. Indica claramente cuál es la alternativa correcta para cada pregunta. Formato deseado: Pregunta, seguido de las alternativas, seguido de la respuesta correcta.\nTexto:\n{text}"
    glossary_prompt = f"Extrae exactamente 5 palabras o términos clave de este texto que podrían ser difíciles de entender para un joven de 15-20 años. Para cada palabra/término, proporciona una breve explicación de su significado en el contexto del texto. Formato deseado: 'Palabra/Término: Explicación.'\nTexto:\n{text}"

    summary = await ask_gemini(summary_prompt)
    explanation = await ask_gemini(explanation_prompt)
    questions_text = await ask_gemini(questions_prompt) # Renamed to avoid conflict
    glossary_text = await ask_gemini(glossary_prompt)   # Renamed to avoid conflict

    return PromptOutput(
        summary=summary.strip(),
        explanation=explanation.strip(),
        questions=[q.strip() for q in questions_text.split("\n") if q.strip()],
        glossary={str(i+1): item.strip() for i, item in enumerate(glossary_text.split("\n")) if item.strip()}
    )

async def assess_text_parameters(text_content: str) -> dict:
    max_chars_for_assessment = 10000 # Example limit
    if len(text_content) > max_chars_for_assessment:
        text_content_for_assessment = text_content[:max_chars_for_assessment] + "..."
        logger.warning(f"Text content truncated to {max_chars_for_assessment} chars for AI assessment.")
    else:
        text_content_for_assessment = text_content

    prompt = f"""
    Analyze the following text and provide an estimation for:
    1. Ideal reading time in seconds for an average reader (e.g., a young adult).
    2. Text difficulty level (choose one: "easy", "medium", "hard").

    Return your response as a single, minified JSON object with two keys:
    - "ideal_time_seconds": An integer representing the estimated reading time in seconds.
    - "difficulty": A string, one of "easy", "medium", or "hard".

    Example JSON output:
    {{"ideal_time_seconds": 300, "difficulty": "medium"}}

    Text for analysis:
    ---
    {text_content_for_assessment}
    ---
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    assessment_results = {"ideal_time_seconds": None, "difficulty": "unknown"}
    json_text_response = "" # Initialize for logging

    try:
        gemini_endpoint_url = GEMINI_URL # Using Gemini Pro for this analysis
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found for text assessment.")
            return assessment_results

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{gemini_endpoint_url}?key={api_key}",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            res.raise_for_status()

        response_data = res.json()
        json_text_response = response_data["candidates"][0]["content"]["parts"][0]["text"]

        if "```json" in json_text_response:
            json_text_response = json_text_response.split("```json")[1].split("```")[0].strip()
        else:
            start_index = json_text_response.find('{')
            end_index = json_text_response.rfind('}')
            if start_index != -1 and end_index != -1 and end_index > start_index:
                json_text_response = json_text_response[start_index:end_index+1]
            else:
                logger.warning(f"Could not reliably extract JSON from Gemini assessment response: {json_text_response}")
                # Keep json_text_response as is for parsing attempt, rely on json.loads to fail if it's not valid

        logger.info(f"Cleaned Gemini JSON response for text assessment: {json_text_response}")
        parsed_data = json.loads(json_text_response)

        if "ideal_time_seconds" in parsed_data and "difficulty" in parsed_data:
            assessment_results["ideal_time_seconds"] = int(parsed_data["ideal_time_seconds"]) if parsed_data["ideal_time_seconds"] is not None else None
            raw_difficulty = parsed_data["difficulty"].lower()
            assessment_results["difficulty"] = raw_difficulty if raw_difficulty in ["easy", "medium", "hard"] else "unknown"
        else:
            logger.warning(f"Gemini assessment output missing expected keys: {parsed_data}")

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling Gemini for text assessment: {e.response.status_code} - {e.response.text}")
    except (json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError) as e:
        logger.error(f"Error parsing Gemini response for text assessment: '{e}'. Response: '{json_text_response}'")
    except Exception as e:
        logger.error(f"Unexpected error in text assessment: {e}")

    return assessment_results


async def get_contextual_assistant_response(query: str, context_text: str) -> str:
    # Basic check for context length if needed, similar to assess_text_parameters
    max_context_chars = 15000 # Example limit for context + query

    # Truncate context_text if it's too long to avoid overly large prompts
    # The query itself is usually short, but context can be large.
    # A more sophisticated approach might summarize context if it's very large.
    if len(context_text) > max_context_chars:
        context_text_for_prompt = context_text[:max_context_chars] + "\n... [context truncated] ..."
        logger.warning(f"Context text truncated to {max_context_chars} chars for AI assistant prompt.")
    else:
        context_text_for_prompt = context_text

    prompt = f"""
    You are a helpful AI assistant. Answer the user's query based *only* on the provided context text.
    If the answer cannot be found in the context text, clearly state that. Do not use external knowledge.

    Context Text:
    ---
    {context_text_for_prompt}
    ---

    User's Query: "{query}"

    Answer:
    """

    # Using the generic ask_gemini function if it's suitable, or make a direct call
    # Assuming ask_gemini is refactored to take a model_url or uses a general one.
    # For simplicity, let's use the direct call pattern here if ask_gemini isn't perfectly matched.

    gemini_endpoint_url = GEMINI_URL # Using Gemini Pro for assistant
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.error("GEMINI_API_KEY not found for assistant.")
        return "Error: AI service is not configured."

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    ai_response_text = "Sorry, I couldn't process your request at the moment."
    response_data_for_logging = None

    try:
        async with httpx.AsyncClient(timeout=45.0) as client: # Timeout for assistant response
            res = await client.post(
                f"{gemini_endpoint_url}?key={api_key}",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            res.raise_for_status()

        response_data_for_logging = res.json()
        # Ensure "candidates" and parts exist before accessing
        if response_data_for_logging.get("candidates") and \
           response_data_for_logging["candidates"][0].get("content") and \
           response_data_for_logging["candidates"][0]["content"].get("parts"):
            ai_response_text = response_data_for_logging["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            logger.warning(f"Unexpected Gemini response structure for assistant: {response_data_for_logging}")
            ai_response_text = "Sorry, I received an unexpected response from the AI."

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling Gemini for assistant: {e.response.status_code} - {e.response.text}")
        ai_response_text = "Error communicating with AI service."
    except (KeyError, IndexError, json.JSONDecodeError) as e: # Added JSONDecodeError just in case
        logger.error(f"Error processing Gemini response for assistant: {e}. Response: {response_data_for_logging if response_data_for_logging else 'N/A'}")
        ai_response_text = "Error processing AI response."
    except Exception as e:
        logger.error(f"Unexpected error in assistant response generation: {e}")
        ai_response_text = "An unexpected error occurred."

    return ai_response_text
