import functools
import logging
import re
import importlib
import os
import subprocess
import json
from typing import Set, Dict, Optional, List
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.router import Router
import time
from datetime import datetime, timedelta
import asyncio
import aiofiles

load_dotenv(dotenv_path='/root/paybots/api.env')

API_TOKEN = os.getenv('API_TOKEN_EPAY')
CHANNEL_ID = int(os.getenv('CHANNEL_ID_EPAY'))
GROUP_ID = int(os.getenv('GROUP_ID_EPAY'))
ADMINS = list(map(int, os.getenv('ADMINS').split(',')))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

STATE_FILE = "/root/paybots/state.json"

# Оптимизированные регулярные выражения
CLEAN_TEXT_PATTERN = re.compile(r"[^\d\s]", re.UNICODE)
BIN_PATTERN = re.compile(r"\b\d{6}(?:\d{10})?\b")

@functools.lru_cache(maxsize=128)
def extract_bins(text: str) -> Set[str]:
    """Кэширование результатов извлечения BIN-кодов"""
    cleaned_text = CLEAN_TEXT_PATTERN.sub("", text.replace("\n", " "))
    numbers = BIN_PATTERN.findall(cleaned_text)
    return {number[:6] for number in numbers if len(number) in [6, 16]} or set()

class BinCache:
    def __init__(self, update_interval: int = 3600):
        self.data: Dict[str, str] = {}
        self.last_update: float = 0
        self.update_interval: int = update_interval
        self.update_lock = asyncio.Lock()

    async def get_data(self, max_retries: int = 3) -> Dict[str, str]:
        """Улучшенный метод получения данных с повторными попытками"""
        for attempt in range(max_retries):
            try:
                async with self.update_lock:
                    if time.time() - self.last_update > self.update_interval:
                        await self.update_cache()
                return self.data
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to get BIN data after {max_retries} attempts: {e}")
                    return {}
                await asyncio.sleep(1)  # Небольшая задержка перед повторной попыткой

    async def update_cache(self, timeout: float = 10.0):
        """Обновление кэша с таймаутом"""
        try:
            await asyncio.wait_for(self._update_cache_impl(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("BIN cache update timed out")

    async def _update_cache_impl(self):
        """Внутренняя реализация обновления кэша"""
        git_pull()
        self.data = reload_bin_data()
        self.last_update = time.time()
        logger.info("BIN cache updated successfully")

class StateManager:
    def __init__(self, save_interval: int = 300):
        self.visited_chats: Set[int] = set()
        self.modified: bool = False
        self.save_interval: int = save_interval
        self.last_save: float = 0
        self.save_lock = asyncio.Lock()

    async def add_chat(self, chat_id: int):
        if chat_id not in self.visited_chats:
            self.visited_chats.add(chat_id)
            self.modified = True
            await self.save_if_needed()

    async def save_if_needed(self):
        async with self.save_lock:
            if self.modified and time.time() - self.last_save > self.save_interval:
                save_state({"visited_chats": list(self.visited_chats)})
                self.modified = False
                self.last_save = time.time()

# Инициализация глобальных объектов
bin_cache = BinCache()
state_manager = StateManager()

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"visited_chats": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

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

def validate_card_number(card_number: str) -> bool:
    """
    Validate card number with flexible input format.
    
    Args:
        card_number (str): Input card number to validate
    
    Returns:
        bool: True if card number is valid, False otherwise
    """
    # Удаляем все пробелы из номера карты
    card_number = card_number.replace(' ', '')
    
    # Проверяем длину номера карты (6 или 16 цифр)
    if len(card_number) not in [6, 16]:
        return False
    
    # Проверяем, состоит ли номер только из цифр
    if not card_number.isdigit():
        return False
    
    return True

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
    for chat_id in state_manager.visited_chats:
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
    try:
        if message.chat.id not in state_manager.visited_chats:
            await state_manager.add_chat(message.chat.id)
            await message.reply("Привет! Я готов помочь вам с определением BIN.")

        # Проверка номера карты перед извлечением BIN
        if validate_card_number(message.text):
            bins = extract_bins(message.text)
            
            if bins:
                bin_data = await bin_cache.get_data()
                if len(bins) > 1:
                    results = [f"{bin_code} - {bin_data.get(bin_code, 'Банк не найден')}" for bin_code in bins]
                    await message.reply("\n".join(results))
                else:
                    bin_code = next(iter(bins))
                    bank_name = bin_data.get(bin_code, "Банк с данным BIN-кодом не найден в базе.")
                    await message.reply(bank_name)

                if message.chat.id == CHANNEL_ID:
                    await forward_to_group(bins, bin_data)
            else:
                # Не выводим сообщение, если BIN не извлечен
                pass
        else:
            # Не выводим сообщение, если номер карты некорректный
            pass

    except Exception as e:
        logging.error(f"Ошибка при обработке сообщения: {e}")
        await message.reply("Произошла ошибка при обработке вашего сообщения.")

async def forward_to_group(bins: Set[str], bin_data: Dict[str, str]):
    try:
        if len(bins) > 1:
            results = [f"{bin_code} - {bin_data.get(bin_code, 'Банк не найден')}" for bin_code in bins]
            await bot.send_message(GROUP_ID, "\n".join(results))
        else:
            bin_code = next(iter(bins))
            bank_name = bin_data.get(bin_code, "Банк с данным BIN-кодом не найден в базе.")
            await bot.send_message(GROUP_ID, bank_name)
    except Exception as e:
        logger.error(f"Error in forward_to_group: {e}")

@router.channel_post()
async def handle_channel_post(message: types.Message):
    try:
        if message.chat.id == CHANNEL_ID:
            bins = extract_bins(message.text)
            if bins:
                bin_data = await bin_cache.get_data()
                await forward_to_group(bins, bin_data)
    except Exception as e:
        logger.error(f"Error in handle_channel_post: {e}")

if __name__ == '__main__':
    bin_data = load_bin_data()
    
    async def periodic_cache_update():
        while True:
            await asyncio.sleep(bin_cache.update_interval)
            await bin_cache.update_cache()
    
    async def periodic_state_save():
        while True:
            await asyncio.sleep(state_manager.save_interval)
            await state_manager.save_if_needed()
    
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_cache_update())
    loop.create_task(periodic_state_save())
    
    dp.run_polling(bot)
