import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = "com.nextbillion.groww"
REVIEW_LANGUAGE = "en"
REVIEW_COUNTRY = "in"
REVIEW_WINDOW_WEEKS = 10
MAX_REVIEWS_PER_FETCH = 1000

MAX_THEMES = 5
TOP_THEMES_IN_PULSE = 3
NUM_QUOTES = 3
NUM_ACTIONS = 3
PULSE_MAX_WORDS = 250

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "qwen/qwen3.8-27b"

EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "")
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID", "")
MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "https://desirable-dedication-production-f08d.up.railway.app",
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
RAW_REVIEWS_PATH = os.path.join(DATA_DIR, "raw_reviews.json")
CLEANED_REVIEWS_PATH = os.path.join(DATA_DIR, "cleaned_reviews.json")
THEMES_PATH = os.path.join(DATA_DIR, "themes.json")
PULSE_PATH = os.path.join(DATA_DIR, "pulse.md")
