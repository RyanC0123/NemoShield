
import os
from pathlib import Path
from dotenv import load_dotenv

# Locate the Backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from Backend/.env
load_dotenv(BASE_DIR / ".env")

# Application configuration
APP_NAME = os.getenv("APP_NAME", "NemoShield")
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

# AI configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
