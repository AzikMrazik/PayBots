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

bin_database = {
    '220001': 'Газпром Банк',
    '220002': 'РНКБ Банк',
    '220003': 'Промсвязь Банк (ПСБ)',
    '220008': 'АБ Россия',
    '220015': 'Альфа-Банк',
    '220028': 'МТС Банк',
    '220030': 'Райффайзен Банк',
    '220048': 'Банк Синара',
    '220064': 'Банк Казани',
    '220070': 'Т-Банк (Тинькофф)',
    '220104': 'Юнистрим',
    '220196': 'ОТП Банк',
    '220220': 'Сбер',
    '220249': 'Солидарность',
    '220383': 'ЭКСИ (МТС деньги)',
    '220431': 'Яндекс Банк'
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

    # Попытка извлечь BIN из сообщения
    bin_code = extract_bin(message.text)
    if bin_code:
        bank_name = bin_database.get(bin_code)
        
        if bank_name:
            logger.info(f"Найден BIN: {bin_code}, название банка: {bank_name}")
            try:
                await asyncio.sleep(0.5)  # Задержка для надежной отправки
                await message.reply(f"{bank_name}")
                logger.info("Сообщение отправлено успешно.")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения: {e}")
        else:
            # Отправка уведомления, если BIN-код не найден в базе
            logger.info("BIN-код не найден в базе данных.")
            try:
                await asyncio.sleep(0.5)
                await message.reply("Банк с данным BIN-кодом не найден в базе. @azikmrazik")
                logger.info("Сообщение об отсутствии BIN-кода в базе отправлено успешно.")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения об отсутствии BIN-кода: {e}")
    else:
        logger.info("BIN-код не обнаружен в сообщении.")

if __name__ == '__main__':
    logger.info("Бот запущен и готов к работе.")
    dp.run_polling(bot)
