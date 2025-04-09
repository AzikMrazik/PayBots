from os import getenv
from dotenv import load_dotenv

load_dotenv(dotenv_path="/root//paybots/api.env")

BOT_TOKEN = getenv("ESP_BOT_TOKEN")
API_TOKEN = getenv("ESP_API_TOKEN")
BASE_URL = getenv("ESP_BASE_URL")
MERCHANT_ID = getenv("ESP_MERCHANT_ID")
DOMAIN = getenv("WH_DOMAIN")
ALLOWED_GROUPS = [int(id.strip()) for id in getenv("ALLOWED_GROUPS", "").split(",") if id.strip()]
ADMINS = [int(id.strip()) for id in getenv("ADMINS", "").split(",") if id.strip()]