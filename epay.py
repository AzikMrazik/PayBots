import logging
import re
import importlib
import os
import subprocess
import json
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.router import Router
from aiogram.filters.command import CommandObject, Command

load_dotenv(dotenv_path='/root/paybots/api.env')

API_TOKEN = os.getenv('API_TOKEN_EPAY')
CHANNEL_ID = int(os.getenv('CHANNEL_ID_EPAY'))
GROUP_ID = int(os.getenv('GROUP_ID_EPAY'))
ADMINS = [831055006]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

STATE_FILE = "/root/paybots/state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"visited_chats": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

state = load_state()
visited_chats = set(state.get("visited_chats", []))

def load_bin_data():
    try:
        importlib.invalidate_caches()
        bin_module = importlib.import_module("BINs")
        return bin_module.bin_database
    except Exception as e:
        logger.error(f"Ошибка при загрузке BIN.py: {e}")
        return {}

def extract_bin(text):
    cleaned_text = re.sub(r"[^\d]", "", text)
    numbers = re.findall(r"\b\d{6,16}\b", cleaned_text)
    for number in numbers:
        return number[:6]
    return None

def git_pull():
    try:
        subprocess.run(["git", "-C", "/root/paybots/", "pull"], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при выполнении git pull:\n{e.stderr}")

@router.message(Command(commands=["send"]))
async def send_broadcast(message: Message, command: CommandObject):
    if message.from_user.id not in ADMINS:
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    if not command.args:
        await message.reply("Введите текст после команды /send.")
        return
    text = command.args
    failed_chats = []
    logger.info(f"Начало рассылки: {text}")
    for chat_id in visited_chats:
        try:
            await bot.send_message(chat_id, text)
            logger.info(f"Сообщение отправлено в чат {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке в чат {chat_id}: {e}")
            failed_chats.append(chat_id)
    if failed_chats:
        await message.reply(f"Рассылка завершена, но не удалось отправить сообщения в {len(failed_chats)} чатов.")
    else:
        await message.reply("Рассылка успешно завершена.")
    logger.info("Рассылка завершена.")

@router.message()
async def handle_message(message: Message):
    if message.text.startswith("/send"):
        return
    if message.chat.id not in visited_chats:
        visited_chats.add(message.chat.id)
        save_state({"visited_chats": list(visited_chats)})
        await message.reply("Привет! Я готов помочь вам с определением BIN.")
    bin_data = load_bin_data()
    bin_code = extract_bin(message.text)
    if bin_code:
        bank_name = bin_data.get(bin_code, "Банк с данным BIN-кодом не найден в базе.")
        await message.reply(bank_name)
        if message.chat.id == CHANNEL_ID:
            await bot.send_message(GROUP_ID, bank_name)
        git_pull()

@router.channel_post()
async def handle_channel_post(message: Message):
    if message.chat.id == CHANNEL_ID:
        bin_data = load_bin_data()
        bin_code = extract_bin(message.text)
        if bin_code:
            bank_name = bin_data.get(bin_code, "Банк с данным BIN-кодом не найден в базе.")
            await bot.send_message(GROUP_ID, bank_name)
            git_pull()

if __name__ == '__main__':
    dp.run_polling(bot)
