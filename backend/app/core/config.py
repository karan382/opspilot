import os

from dotenv import load_dotenv

load_dotenv()


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY is not configured")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://opspilot:opspilot_dev@localhost:5432/opspilot",
)

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://localhost:6333",
)

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000",
).split(",")