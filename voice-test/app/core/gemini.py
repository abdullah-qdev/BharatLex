import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("Gemini key loaded:", api_key[:10])

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing in environment variables")

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-3.5-flash")