from os import getenv
from dotenv import load_dotenv

load_dotenv(dotenv_path="/root/PayBots/api.env")

BOT_TOKEN = getenv("BC_BOT_TOKEN")