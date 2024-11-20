import logging
import re
import importlib
import os
import subprocess
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.router import Router

# Загружаем переменные окружения
load_dotenv(dotenv_path='/root/paybots/api.env')

API_TOKEN = os.getenv('API_TOKEN_EPAY')

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Импортируем BIN-данные из внешнего файла
def load_bin_data():
    try:
        bin_module = importlib.import_module("BINs")  # Убедитесь, что файл называется BINs.py
        logger.info("BINs.py успешно загружен.")
        return bin_module.bin_database
    except ModuleNotFoundError:
        logger.error("Файл BIN.py не найден. Проверьте, находится ли он в той же директории, что и бот.")
        return {}
    except Exception as e:
        logger.error(f"Ошибка при загрузке BIN.py: {e}")
        return {}

def extract_bin(text):
    """
    Ищет шестизначный BIN-код в тексте и фильтрует по диапазону 220000-220500.
    """
    cleaned_text = re.sub(r"[^\d\s]", "", text)  # Убираем все нечисловые символы, кроме пробелов
    logger.info(f"Очищенный текст для поиска BIN: {cleaned_text}")

    # Разделяем текст на числа
    numbers = re.findall(r"\b\d{6,16}\b", cleaned_text)  # Ищем числа длиной 6-16 символов (например, карты)
    for number in numbers:
        bin_candidate = number[:6]  # Берем первые 6 цифр каждого числа
        if 220000 <= int(bin_candidate) <= 220500:  # Проверяем диапазон BIN-кодов
            logger.info(f"Найден BIN: {bin_candidate}")
            return bin_candidate
    logger.info("BIN-код не найден после проверки диапазона.")
    return None

def git_pull():
    """
    Выполняет команду git pull в папке /root/paybots/
    """
    try:
        result = subprocess.run(
            ["git", "-C", "/root/paybots/", "pull"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Git pull выполнен успешно:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при выполнении git pull:\n{e.stderr}")

@router.message()
async def handle_message(message: Message):
    logger.info(f"Получено сообщение из чата {message.chat.id}")
    logger.info(f"Текст сообщения: {message.text}")

    # Проверка, что текст в сообщении присутствует
    if message.text is None:
        logger.info("Сообщение не содержит текст, пропуск обработки.")
        return

    bin_data = load_bin_data()  # Загружаем BIN-данные при каждом сообщении
    bin_code = extract_bin(message.text)
    if bin_code:
        bank_name = bin_data.get(bin_code, "Банк с данным BIN-кодом не найден в базе.")
        try:
            # Отправка ответа пользователю или в чат
            await message.reply(bank_name)
            logger.info("Сообщение о банке отправлено.")
            git_pull()  # Выполняем git pull после отправки сообщения
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")

if __name__ == '__main__':
    logger.info("Бот запущен и готов к работе.")
    dp.run_polling(bot)
