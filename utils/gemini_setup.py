# utils/gemini_setup.py
import os
from crewai.llm import LLM
from dotenv import load_dotenv

load_dotenv()

class GeminiSetup:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    def get_llm(self) -> LLM:
        """Get CrewAI compatible Gemini LLM"""
        return LLM(
            model="gemini/gemini-2.0-flash",  # You can also use "gemini/gemini-1.5-pro"
            api_key=self.api_key,
            temperature=0.1
        )

# Create global instance
gemini_setup = GeminiSetup()