import logging
import re
import importlib
import os
import json
import subprocess
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.router import Router
from aiogram.filters import Command

# Загружаем переменные окружения
load_dotenv(dotenv_path='/root/paybots/api.env')

API_TOKEN = os.getenv('API_TOKEN_EPAY')

# Список ID администраторов
ADMIN_IDS = [831055006, 5583033210]  # Ваши ID

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Путь к файлу для хранения списка чатов
CHAT_STORAGE_PATH = '/root/paybots/chat_list.json'

# Определение функции load_bin_data
def load_bin_data():
    """
    Загружает данные из BINs.py.
    """
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

# Остальной код
def save_chat(chat_id):
    """
    Сохраняет ID чата в локальном JSON-файле.
    """
    try:
        if not os.path.exists(CHAT_STORAGE_PATH):
            with open(CHAT_STORAGE_PATH, 'w') as f:
                json.dump([], f)

        with open(CHAT_STORAGE_PATH, 'r') as f:
            chats = json.load(f)

        if chat_id not in chats:
            chats.append(chat_id)
            with open(CHAT_STORAGE_PATH, 'w') as f:
                json.dump(chats, f)
            logger.info(f"Добавлен новый чат: {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении чата: {e}")

def load_chats():
    """
    Загружает список ID чатов из локального JSON-файла.
    """
    try:
        if not os.path.exists(CHAT_STORAGE_PATH):
            return []
        with open(CHAT_STORAGE_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при загрузке чатов: {e}")
        return []

# Все функции и обработчики определяются ниже
@router.message()
async def handle_message(message: Message):
    """
    Основной обработчик сообщений.
    """
    logger.info(f"Получено сообщение из чата {message.chat.id}")
    logger.info(f"Текст сообщения: {message.text}")

    # Сохраняем ID чата для рассылки
    save_chat(message.chat.id)

    # Проверка, что текст в сообщении присутствует
    if message.text is None:
        logger.info("Сообщение не содержит текст, пропуск обработки.")
        return

    bin_code = extract_bin(message.text)
    if bin_code:
        bank_name = load_bin_data().get(bin_code, "Банк с данным BIN-кодом не найден в базе.")
        try:
            await message.reply(bank_name)
            logger.info("Сообщение о банке отправлено.")
            git_pull()  # Выполняем git pull после отправки сообщения
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")

if __name__ == '__main__':
    logger.info("Бот запущен и готов к работе.")
    dp.run_polling(bot)
