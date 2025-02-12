from os import getenv
from dotenv import load_dotenv

load_dotenv(dotenv_path="C:/Programming/PayBots/api.env")

BOT_TOKEN = getenv("CP_BOT_TOKEN")
API_TOKEN = getenv("CP_API_TOKEN")
BASE_URL = getenv("CP_BASE_URL")
MERCHANT_TOKEN = getenv("CP_MERCHANT_TOKEN")
MERCHANT_ID = getenv("CP_MERCHANT_ID")
ALLOWED_GROUPS = [int(id.strip()) for id in getenv("ALLOWED_GROUPS", "").split(",") if id.strip()]
