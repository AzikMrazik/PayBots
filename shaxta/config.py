from os import getenv
from dotenv import load_dotenv

load_dotenv(dotenv_path="/root/paybots/api.env")

BOT_TOKEN = getenv("SX_BOT_TOKEN")
API_TOKEN = getenv("SX_API_TOKEN")
BASE_URL = getenv("SX_BASE_URL")
ALLOWED_GROUPS = [int(id.strip()) for id in getenv("ALLOWED_GROUPS", "").split(",") if id.strip()]