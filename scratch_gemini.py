import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='Give me a valid JSON object {"status": "ok"}',
    )
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")
