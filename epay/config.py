from os import getenv
from dotenv import load_dotenv

load_dotenv(dotenv_path="/root/paybots/api.env")

BOT_TOKEN = getenv("EP_BOT_TOKEN")
API_TOKEN = getenv("EP_API_TOKEN")
BASE_URL = getenv("EP_BASE_URL")
PAYOUT_API = getenv("EP_PAYOUT_API")
DOMAIN = getenv("WH_DOMAIN")
ALLOWED_GROUPS = [int(id.strip()) for id in getenv("ALLOWED_GROUPS", "").split(",") if id.strip()]
ADMINS = [int(id.strip()) for id in getenv("ADMINS", "").split(",") if id.strip()]