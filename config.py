"""Central configuration. Reads values from the .env file."""
import os
from dotenv import load_dotenv

load_dotenv()

# Absolute path to this project folder, so the DB file is always found
# no matter where the app is launched from.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Groq AI
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # SQLite — a single file stored next to the app. No server, no password.
    # `or` handles the case where DB_PATH is present but blank in .env.
    DB_PATH = os.getenv("DB_PATH") or os.path.join(BASE_DIR, "event_planner.db")

    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
