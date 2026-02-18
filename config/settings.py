import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    HEADLESS_MODE = os.getenv("HEADLESS_MODE", "true").lower() == "true"
    BROWSER_TYPE = os.getenv("BROWSER_TYPE", "chromium")
    USER_DATA_DIR = os.getenv("USER_DATA_DIR", "./user_data")

settings = Settings()
