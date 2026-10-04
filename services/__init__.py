import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-3.5-flash-lite"

MAX_RETRIES = 3
RETRY_DELAY = 2


def generate_content(prompt):
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            return response.text.strip()

        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise e

            print(
                f"Gemini request failed "
                f"(attempt {attempt + 1}/{MAX_RETRIES}): {e}"
            )

            time.sleep(RETRY_DELAY * (2 ** attempt))