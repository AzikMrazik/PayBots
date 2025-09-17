from os import getenv
from dotenv import load_dotenv

load_dotenv(dotenv_path="/root/paybots/api.env")

BOT_TOKEN = getenv("AP_BOT_TOKEN")
API_TOKEN = getenv("AP_API_TOKEN")
BASE_URL = getenv("AP_BASE_URL")
DOMAIN = getenv("WH_DOMAIN")
ALLOWED_GROUPS = [int(id.strip()) for id in getenv("ALLOWED_GROUPS", "").split(",") if id.strip()]