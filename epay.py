import logging
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage

API_TOKEN = '7354054366:AAHDb7f5ggIJJMESBRscwVkw12oX2dRzfG0'

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ID канала и группы
CHANNEL_ID = 2415709971
GROUP_ID = -1002486163462

bin_database = {
    '220001': 'Газпромбанк',
    '220003': 'Промсвязьбанк (ПСБ)',
    '220008': 'АБ Россия',
    '220015': 'Альфа-Банк',
    '220220': 'Сбер',
    # Добавьте остальные BIN-коды
}

def extract_bin(text):
    # Убираем все пробелы в номере карты и проверяем, есть ли 6 цифр в начале
    cleaned_text = re.sub(r"\s+", "", text)  # Убираем пробелы
    match = re.match(r"\b\d{6}", cleaned_text)  # Проверяем только первые 6 цифр
    return match.group(0) if match else None

@dp.message()
async def handle_message(message: Message):
    logger.info(f"Получено сообщение от {message.from_user.username} ({message.from_user.id}) в чате {message.chat.id}")
    logger.info(f"Текст сообщения: {message.text}")

    # Проверка, что текст в сообщении присутствует
    if message.text is None:
        logger.info("Сообщение не содержит текст, пропуск обработки.")
        return

    # Проверка сообщений из канала
    if message.chat.id == CHANNEL_ID:
        bin_code = extract_bin(message.text)
        if bin_code:
            bank_name = bin_database.get(bin_code, "Банк с данным BIN-кодом не найден в базе.")
            try:
                # Отправка в группу
                await bot.send_message(GROUP_ID, f"BIN: {bin_code}, Банк: {bank_name}")
                logger.info("Сообщение о банке отправлено в группу.")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения в группу: {e}")

if __name__ == '__main__':
    logger.info("Бот запущен и готов к работе.")
    dp.run_polling(bot)
