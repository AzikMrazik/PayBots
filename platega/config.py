from os import getenv
from dotenv import load_dotenv

load_dotenv(dotenv_path="/root/paybots/api.env")

BOT_TOKEN = getenv("P_BOT_TOKEN")
API_KEY = getenv("P_API_KEY")
MERCHANT_ID = getenv("P_MERCHANT_ID")
BASE_URL = getenv("P_BASE_URL")
ALLOWED_GROUPS = [int(id.strip()) for id in getenv("ALLOWED_GROUPS", "").split(",") if id.strip()]
RUB_ID = 0