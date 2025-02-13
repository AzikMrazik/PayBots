from dotenv import load_dotenv
from os import getenv

load_dotenv(dotenv_path="/root/paybots/api.env")

BOT_TOKEN = getenv("WH_BOT_TOKEN")
DOMAIN = getenv("WH_DOMAIN")
ALLOWED_GROUPS = [int(id.strip()) for id in getenv("ALLOWED_GROUPS", "").split(",") if id.strip()]