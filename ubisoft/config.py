from os import getenv
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")
TECH_ID = int(getenv("TECH_ID", "831055006"))  # Default to 0 if not set
DOMAIN = getenv("DOMAIN", "paybots.shop")  # Default to example.com if not set