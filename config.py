import os
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address

# --- Load Environment Variables ---
load_dotenv(override=True)
BASE_URL = os.getenv("URL")
MODEL_NAME = os.getenv("MODEL")
API_KEY = os.getenv("KEY")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
USER_API_KEY = os.getenv("USER_API_KEY")

# --- Rate Limiting ---
limiter = Limiter(key_func=get_remote_address)