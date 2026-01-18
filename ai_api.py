import os
from dotenv import load_dotenv
from google import genai
import time
#from google.genai.errors import ClientError,ServerError,
from google.genai.errors import ClientError, ServerError, APIError


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing")

client = genai.Client(api_key=API_KEY)

MODEL = "models/gemini-2.5-flash-lite"

def query_ai(prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={
                "temperature": 0.4,
                "max_output_tokens": 1400
            }
        )
        return response.text
    except ClientError as e:
        code = getattr(e, "code", None)

        # 429 – Quota exceeded
        if code == 429:
            time.sleep(30)
            return "⚠️ AI is busy due to high usage. Please try again in a minute."

        # 400 – Bad request / prompt too long
        if code == 400:
            return "⚠️ Request is too large. Please try a shorter message."

        # 401 / 403 – API key / permission issues
        if code in (401, 403):
            return "⚠️ AI access issue. Please contact the administrator."

        # 404 – Model / endpoint issue
        if code == 404:
            return "⚠️ AI model is temporarily unavailable. Please try later."

        # Any other client error (future-proof)
        return "⚠️ AI could not process your request. Please try again."
    
    except ServerError:
        # 503 – Server overloaded
        return "⚠️ AI servers are overloaded right now. Please try again shortly."

    except APIError:
        # Any other Gemini API error
        return "⚠️ AI service is temporarily unavailable. Please try again later."

    except Exception:
        # Absolute safety net (never crash UI)
        return "⚠️ Something went wrong. Please refresh the page and try again."

    