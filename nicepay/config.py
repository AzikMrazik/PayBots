from dotenv import load_dotenv
from os import getenv

load_dotenv(dotenv_path="/root/paybots/api.env")

BOT_TOKEN = getenv("NP_BOT_TOKEN")
SECRET = getenv("NP_SECRET")
MERCHANT_ID = getenv("NP_MERCHANT_ID")
BASE_URL = getenv("NP_BASE_URL")
ALLOWED_GROUPS = [int(id.strip()) for id in getenv("ALLOWED_GROUPS", "").split(",") if id.strip()]