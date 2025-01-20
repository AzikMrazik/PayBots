from os import getenv
from dotenv import load_dotenv

load_dotenv(dotenv_path="/root/paybots/api.env")

BOT_TOKEN = getenv("BOT_TOKEN_CASHINOUT")
API_TOKEN = getenv("API_TOKEN_CASHINOUT")
BASE_URL = getenv("BASE_URL")
PAY_URL = getenv("PAY_URL")
UNIQUE_ID = int(getenv("UNIQUE_ID"))
UNIQUE_NAME = getenv("UNIQUE_NAME")
ADMIN_ID = [int(id.strip()) for id in getenv("ADMIN_ID").split(",")]
ALLOWED_GROUPS = [int(id.strip()) for id in getenv("ALLOWED_GROUPS", "").split(",")]
RUB_ID = int(getenv("RUB_ID"))