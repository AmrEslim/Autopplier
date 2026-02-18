import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
    LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    HEADLESS_MODE = os.getenv("HEADLESS_MODE", "False").lower() == "true"

settings = Settings()
