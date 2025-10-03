import asyncio
from decimal import Decimal

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from config import get_settings
from database import Database
from api_client import RefeeApiClient
from handlers.balance import router as balance_router
from handlers.purchase import router as purchase_router
from handlers.wallet import router as wallet_router
from handlers.start import router as start_router


async def setup_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Приветствие и описание"),
        BotCommand(command="balance", description="Показать баланс"),
        BotCommand(command="refill", description="Пополнить баланс"),
        BotCommand(command="buyenergy", description="Купить энергию Tron"),
        BotCommand(command="buybandwidth", description="Купить bandwidth Tron"),
        BotCommand(command="calculate", description="Рассчитать энергию/стоимость"),
        BotCommand(command="addwallet", description="Сохранить адрес Tron"),
        BotCommand(command="mywallets", description="Мои кошельки"),
    ]
    await bot.set_my_commands(commands)


async def main() -> None:
    settings = get_settings()
    logger.info("Starting RF x TSA bot")

    db = Database(settings.database_path)
    await db.initialize()

    api = RefeeApiClient(settings.refee_api_key, settings.api_base_url)

    bot = Bot(token=settings.bot_token, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())

    # Inject shared dependencies via context
    dp["db"] = db
    dp["api"] = api

    dp.include_router(start_router)
    dp.include_router(balance_router)
    dp.include_router(purchase_router)
    dp.include_router(wallet_router)

    await setup_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

