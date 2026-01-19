import streamlit as st
from google import genai
from google.genai.errors import ClientError, ServerError, APIError

# ---------------- API KEY ----------------

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except KeyError:
    st.error("❌ AI configuration missing. Please contact administrator.")
    st.stop()

# ---------------- CLIENT ----------------

client = genai.Client(api_key=API_KEY)

MODEL = "models/gemini-2.5-flash-lite"

# ---------------- QUERY FUNCTION ----------------

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

        if code == 429:
            return "⚠️ AI is busy due to high usage. Please try again in a minute."

        if code == 400:
            return "⚠️ Request is too large. Please shorten your message."

        if code in (401, 403):
            return "⚠️ AI access issue. Please contact the administrator."

        if code == 404:
            return "⚠️ AI model is temporarily unavailable. Please try later."

        return "⚠️ AI could not process your request. Please try again."

    except ServerError:
        return "⚠️ AI servers are overloaded right now. Please try again shortly."

    except APIError:
        return "⚠️ AI service is temporarily unavailable. Please try again later."

    except Exception:
        return "⚠️ Something went wrong. Please refresh the page and try again."

