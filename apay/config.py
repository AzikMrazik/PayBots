from os import getenv
from dotenv import load_dotenv

load_dotenv(dotenv_path="/root/paybots/api.env")

BOT_TOKEN = getenv("AP_BOT_TOKEN")
SECRET_KEY = getenv("AP_SECRET_KEY")
BASE_URL = getenv("AP_BASE_URL")
CLIENT_ID = getenv("AP_CLIENT_ID")
ALLOWED_GROUPS = [int(id.strip()) for id in getenv("ALLOWED_GROUPS", "").split(",") if id.strip()]
RUB_ID = 0