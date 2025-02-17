from os import getenv
from dotenv import load_dotenv

load_dotenv(dotenv_path="/root/paybots/api.env")

BOT_TOKEN = getenv("CR_BOT_TOKEN")
ID = getenv("CR_ID")
SECRET = getenv("CR_SECRET")
DOMAIN = getenv("WH_DOMAIN")
BASE_URL = getenv("CR_BASE_URL")
ALLOWED_GROUPS = [int(id.strip()) for id in getenv("ALLOWED_GROUPS", "").split(",") if id.strip()]
ADMINS = [int(id.strip()) for id in getenv("ADMINS", "").split(",") if id.strip()]
