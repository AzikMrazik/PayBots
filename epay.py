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

@router.message(Command(commands=["start"]))
async def send_welcome(message: Message):
    """
    Отправляет приветственное сообщение при команде /start.
    """
    save_chat(message.chat.id)  # Сохраняем ID чата
    await message.reply("Привет! Отправь номер карты, и я скажу название банка.")

@router.message(Command(commands=["broadcast"]))
async def broadcast_message(message: Message):
    """
    Функционал рассылки сообщений для администраторов.
    """
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("У вас нет доступа к этой функции.")
        return

    # Текст рассылки (убираем команду /broadcast)
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.reply("Пожалуйста, введите текст для рассылки после команды /broadcast.")
        return

    await message.reply("Начинаю рассылку...")

    # Загружаем список чатов
    chat_ids = load_chats()

    success_count = 0
    error_count = 0

    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id, text)
            success_count += 1
        except Exception as e:
            logger.error(f"Ошибка отправки в чат {chat_id}: {e}")
            error_count += 1

    await message.reply(f"Рассылка завершена. Успешно: {success_count}, Ошибки: {error_count}.")

@router.message()
async def handle_message(message: Message):
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
