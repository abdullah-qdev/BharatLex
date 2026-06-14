import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class LazyGroqClient:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise RuntimeError("GROQ_API_KEY is not set. Add it to voice-test/.env before using AI analysis.")
            self._client = Groq(api_key=api_key)
        return self._client

    def __getattr__(self, name):
        return getattr(self._get_client(), name)


client = LazyGroqClient()
