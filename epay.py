import logging
import re
import importlib
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.router import Router

API_TOKEN = '7354054366:AAHDb7f5ggIJJMESBRscwVkw12oX2dRzfG0'

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# ID канала и группы
CHANNEL_ID = -1002415709971
GROUP_ID = -1002486163462

# Импортируем BIN-данные из внешнего файла
def load_bin_data():
    try:
        bin_module = importlib.import_module("BIN")
        return bin_module.bin_database
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

@router.channel_post()
async def handle_channel_post(message: Message):
    logger.info(f"Получено сообщение из канала {message.chat.id}")
    logger.info(f"Текст сообщения: {message.text}")

    # Проверка, что текст в сообщении присутствует
    if message.text is None:
        logger.info("Сообщение не содержит текст, пропуск обработки.")
        return

    # Проверка сообщений из канала
    if message.chat.id == CHANNEL_ID:
        logger.info("Сообщение поступило из целевого канала.")
        bin_data = load_bin_data()  # Загружаем BIN-данные при каждом сообщении
        bin_code = extract_bin(message.text)
        if bin_code:
            bank_name = bin_data.get(bin_code, "Банк с данным BIN-кодом не найден в базе.")
            try:
                # Отправка сообщения только в группу
                await bot.send_message(GROUP_ID, bank_name)
                logger.info("Сообщение о банке отправлено в группу.")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения в группу: {e}")
        else:
            logger.info("BIN-код не найден в тексте сообщения.")

if __name__ == '__main__':
    logger.info("Бот запущен и готов к работе.")
    dp.run_polling(bot)
