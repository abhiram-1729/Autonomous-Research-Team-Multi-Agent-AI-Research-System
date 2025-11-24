# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Gemini model configuration
    MODEL = "gemini-2.0-flash"
    MODEL_TEMPERATURE = 0.1
    
settings = Settings()