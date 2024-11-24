import logging
import re
import importlib
import os
import subprocess
import shelve
import json
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.router import Router
import fcntl

load_dotenv(dotenv_path='/root/paybots/api.env')

API_TOKEN = os.getenv('API_TOKEN_EPAY')
CHANNEL_ID = int(os.getenv('CHANNEL_ID_EPAY'))
GROUP_ID = int(os.getenv('GROUP_ID_EPAY'))
ADMINS = list(map(int, os.getenv('ADMINS').split(',')))
STATE_FILE = "/root/paybots/epay_state.json"
BACKUP_STATE_FILE = "/root/paybots/epay_state_backup.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

def atomic_write(filename, data):
    try:
        temp_filename = filename + '.tmp'
        with open(temp_filename, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        os.replace(temp_filename, filename)
    except Exception as e:
        logger.error(f"Ошибка при атомарной записи: {e}")

def load_visited_chats():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return set(json.load(f))
        elif os.path.exists(BACKUP_STATE_FILE):
            with open(BACKUP_STATE_FILE, 'r') as f:
                return set(json.load(f))
        return set()
    except Exception as e:
        logger.error(f"Ошибка загрузки посещенных чатов: {e}")
        return set()

def save_visited_chats(visited_chats):
    try:
        atomic_write(STATE_FILE, list(visited_chats))
        atomic_write(BACKUP_STATE_FILE, list(visited_chats))
    except Exception as e:
        logger.error(f"Ошибка сохранения посещенных чатов: {e}")

visited_chats = load_visited_chats()

def load_bin_data():
    try:
        importlib.invalidate_caches()
        bin_module = importlib.import_module("BINs")
        return bin_module.bin_database
    except Exception as e:
        logger.error(f"Ошибка при загрузке BIN.py: {e}")
        return {}

def reload_bin_data():
    try:
        importlib.invalidate_caches()
        bin_module = importlib.import_module("BINs")
        importlib.reload(bin_module)
        return bin_module.bin_database
    except Exception as e:
        logger.error(f"Ошибка при перезагрузке BIN.py: {e}")
        return {}

def git_pull():
    try:
        result = subprocess.run(["git", "-C", "/root/paybots/", "pull"], capture_output=True, text=True, check=True)
        logger.info(f"Результат git pull:\n{result.stdout}")
        globals()["bin_data"] = reload_bin_data()
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при выполнении git pull:\n{e.stderr}")

def extract_bins(text):
    cleaned_text = re.sub(r"[^\d\s]", "", text.replace("\n", " "))
    numbers = re.findall(r"\b\d{6}(?:\d{10})?\b", cleaned_text)
    bins = {number[:6] for number in numbers if len(number) in [6, 16]}
    return bins if bins else None

@router.message(Command("send"))
async def send_broadcast(message: types.Message):
    if message.from_user.id not in ADMINS:
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    text = message.text.partition(" ")[2]
    if not text:
        await message.reply("Введите текст после команды /send.")
        return
    failed_chats = []
    for chat_id in visited_chats:
        try:
            await bot.send_message(chat_id, text)
        except Exception:
            failed_chats.append(chat_id)
    if failed_chats:
        await message.reply(f"Рассылка завершена, но не удалось отправить сообщения в {len(failed_chats)} чатов.")
    else:
        await message.reply("Рассылка успешно завершена.")

@router.message()
async def handle_message(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in visited_chats:
        visited_chats.add(chat_id)
        save_visited_chats(visited_chats)
        await message.reply("Привет! Я готов помочь вам с определением BIN.")
    
    bins = extract_bins(message.text)
    if bins:
        if len(bins) > 1:
            results = [f"{bin_code} - {bin_data.get(bin_code, 'Банк не найден')}" for bin_code in bins]
            await message.reply("\n".join(results))
        else:
            bin_code = next(iter(bins))
            bank_name = bin_data.get(bin_code, "Банк с данным BIN-кодом не найден в базе.")
            await message.reply(bank_name)
        
        if chat_id == CHANNEL_ID:
            if len(bins) > 1:
                results = [f"{bin_code} - {bin_data.get(bin_code, 'Банк не найден')}" for bin_code in bins]
                await bot.send_message(GROUP_ID, "\n".join(results))
            else:
                bin_code = next(iter(bins))
                bank_name = bin_data.get(bin_code, "Банк с данным BIN-кодом не найден в базе.")
                await bot.send_message(GROUP_ID, bank_name)
        git_pull()

@router.channel_post()
async def handle_channel_post(message: types.Message):
    if message.chat.id == CHANNEL_ID:
        bins = extract_bins(message.text)
        if bins:
            if len(bins) > 1:
                results = [f"{bin_code} - {bin_data.get(bin_code, 'Банк не найден')}" for bin_code in bins]
                await bot.send_message(GROUP_ID, "\n".join(results))
            else:
                bin_code = next(iter(bins))
                bank_name = bin_data.get(bin_code, "Банк с данным BIN-кодом не найден в базе.")
                await bot.send_message(GROUP_ID, bank_name)
            git_pull()

if __name__ == '__main__':
    bin_data = load_bin_data()
    dp.run_polling(bot)
