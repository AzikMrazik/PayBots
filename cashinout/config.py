from os import getenv
from dotenv import load_dotenv

load_dotenv(dotenv_path="/root/paybots/api.env")

BOT_TOKEN = getenv("CIO_BOT_TOKEN")
API_TOKEN = getenv("CIO_API_TOKEN")
BASE_URL = getenv("CIO_BASE_URL")
PAY_URL = getenv("CIO_PAY_URL")
WEB_SERVER_IP = getenv("WEB_SERVER_IP")
WEB_SERVER_PORT = int(getenv("WEB_SERVER_PORT")) 
ALLOWED_GROUPS = [int(id.strip()) for id in getenv("ALLOWED_GROUPS", "").split(",") if id.strip()]
RUB_ID = 0