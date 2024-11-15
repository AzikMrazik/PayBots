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
    '220006': 'Связь-Банк. @azikmrazik',
    '220008': 'АБ Россия',
    '220009': 'Челябинвестбанк. @azikmrazik',
    '220011': 'Банк Левобережный. @azikmrazik',
    '220013': 'Западно-Сибирский коммерческий банк. @azikmrazik',
    '220014': 'Кредитно-Страховой Банк (КС Банк). @azikmrazik',
    '220015': 'Альфа-Банк',
    '220016': 'Челябинвестбанк. @azikmrazik',
    '220017': 'Центр-инвест Банк. @azikmrazik',
    '220018': 'Севергазбанк. @azikmrazik',
    '220020': 'Московский Индустриальный Банк. @azikmrazik',
    '220021': 'Банк Александровский. @azikmrazik',
    '220022': 'МДМ Банк. @azikmrazik',
    '220023': 'Авангард Банк. @azikmrazik',
    '220024': 'ВТБ24. @azikmrazik',
    '220025': 'СДМ Банк. @azikmrazik',
    '220028': 'МТС Банк',
    '220030': 'Райффайзен Банк',
    '220038': 'Россельхозбанк. @azikmrazik',
    '220041': 'Алмазэргиэнбанк. @azikmrazik',
    '220042': 'Дальневосточный Банк. @azikmrazik',
    '220043': 'Финансовая Корпорация Открытие. @azikmrazik',
    '220048': 'Банк Синара',
    '220050': 'Московский Кредитный Банк (МКБ). @azikmrazik',
    '220051': 'Транскапиталбанк. @azikmrazik',
    '220055': 'Уральский Банк Реконструкции и Развития (УБРиР). @azikmrazik',
    '220058': 'Совкомбанк. @azikmrazik',
    '220064': 'Банк Казани',
    '220065': 'Национальный Банк Траст. @azikmrazik',
    '220070': 'Т-Банк (Тинькофф)',
    '220071': 'РосЕвроБанк. @azikmrazik',
    '220080': 'Восточный Банк. @azikmrazik',
    '220089': 'Юникредит Банк. @azikmrazik',
    '220093': 'Абсолют Банк. @azikmrazik',
    '220096': 'Трансстройбанк. @azikmrazik',
    '220102': 'Инвестиционный Союз Банк. @azikmrazik',
    '220104': 'Юнистрим',
    '220105': 'Северный Морской Путь Банк (СМП Банк). @azikmrazik',
    '220108': 'Банк Пересвет. @azikmrazik',
    '220112': 'Росэнергобанк. @azikmrazik',
    '220121': 'Национальный Резервный Банк (НРБ). @azikmrazik',
    '220126': 'Креди Агриколь КИБ Банк. @azikmrazik',
    '220131': 'Русский Стандарт. @azikmrazik',
    '220135': 'Энерготрансбанк. @azikmrazik',
    '220140': 'Хоум Кредит Банк. @azikmrazik',
    '220144': 'Джей энд Ти Банк. @azikmrazik',
    '220149': 'Южный Региональный Банк. @azikmrazik',
    '220156': 'Уральский Банк. @azikmrazik',
    '220161': 'Ак Барс Банк. @azikmrazik',
    '220165': 'Банк Зенит. @azikmrazik',
    '220172': 'Кубань Кредит Банк. @azikmrazik',
    '220175': 'Райффайзен Лизинг. @azikmrazik',
    '220183': 'ВТБ (Внешторгбанк). @azikmrazik',
    '220192': 'Сургутнефтегазбанк. @azikmrazik',
    '220194': 'Кредит Европа Банк. @azikmrazik',
    '220195': 'Кранбанк. @azikmrazik',
    '220196': 'ОТП Банк',
    '220200': 'Союз Банк. @azikmrazik',
    '220208': 'Металлинвестбанк. @azikmrazik',
    '220213': 'Интерпромбанк. @azikmrazik',
    '220218': 'Международный Финансовый Клуб. @azikmrazik',
    '220220': 'Сбер',
    '220230': 'Северная Казна. @azikmrazik',
    '220234': 'Росдорбанк. @azikmrazik',
    '220240': 'Номос Банк. @azikmrazik',
    '220249': 'Солидарность',
    '220250': 'АИКБ Банк Сибэс. @azikmrazik',
    '220255': 'Авангард Экспресс Банк. @azikmrazik',
    '220259': 'Национальный Клиринговый Центр. @azikmrazik',
    '220267': 'Русский Торговый Банк. @azikmrazik',
    '220278': 'Сибирский Банк. @azikmrazik',
    '220285': 'ПромТрансБанк. @azikmrazik',
    '220292': 'Запсибкомбанк. @azikmrazik',
    '220301': 'ОАО Нефтяной Банк. @azikmrazik',
    '220320': 'Примсоцбанк. @azikmrazik',
    '220328': 'Москомприватбанк. @azikmrazik',
    '220329': 'Центральный Банк. @azikmrazik',
    '220330': 'Русславбанк. @azikmrazik',
    '220340': 'Гута Банк. @azikmrazik',
    '220344': 'Новикомбанк. @azikmrazik',
    '220350': 'Генбанк. @azikmrazik',
    '220355': 'Альфа-Страхование. @azikmrazik',
    '220356': 'Национальный Страховой Банк. @azikmrazik',
    '220358': 'Русьбанк. @azikmrazik',
    '220370': 'СКБ-банк. @azikmrazik',
    '220374': 'Банк Возрождение. @azikmrazik',
    '220380': 'Советский Банк. @azikmrazik',
    '220381': 'Промсвязьбанк. @azikmrazik',
    '220383': 'ЭКСИ (МТС деньги)',
    '220431': 'Яндекс Банк',
    '220432': 'Озон (OZON) Банк'
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
