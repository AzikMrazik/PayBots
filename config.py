import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    bot_token: str
    refee_api_key: str
    database_path: str = "/workspace/rf_x_tsa.db"
    api_base_url: str = "https://api.refee.bot"


def get_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "")
    refee_api_key = os.getenv("REFEE_API_KEY", os.getenv("API_KEY", ""))
    database_path = os.getenv("DATABASE_PATH", "/workspace/rf_x_tsa.db")
    api_base_url = os.getenv("API_BASE_URL", "https://api.refee.bot")

    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set in environment")
    if not refee_api_key:
        raise RuntimeError("REFEE_API_KEY (or API_KEY) is not set in environment")

    return Settings(
        bot_token=bot_token,
        refee_api_key=refee_api_key,
        database_path=database_path,
        api_base_url=api_base_url,
    )

