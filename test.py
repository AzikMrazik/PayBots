import asyncio
import logging
from pyrogram import Client, filters

logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования (DEBUG для подробных логов)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Ваши данные
api_id = 27482634  # Замените на ваш API ID
api_hash = "92944e4f562f1566af62e033a2e94864"  # Замените на ваш API Hash
session_name = "boter"  # Имя сессии

# ID чатов
source_chat_id = -1002486163462 # ID группы (источник)
target_channel_id = -1002415709971  # ID канала (назначение)

# Инициализация клиента
app = Client(session_name, api_id=api_id, api_hash=api_hash)

@app.on_message(filters.chat(source_chat_id))
async def forward_message(client, message):
    try:
        logger.info(f"Получено сообщение: {message.text}")
        await client.forward_messages(chat_id=target_channel_id, from_chat_id=message.chat.id, message_ids=message.id)
        logger.info(f"Сообщение переслано: {message.text}")
    except Exception as e:
        logger.error(f"Ошибка при пересылке сообщения: {e}")

async def main():
    try:
        await app.start()
        logger.info("Клиент запущен и готов к работе.")
        await asyncio.Event().wait()  # Бесконечное ожидание
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
    finally:
        await app.stop()
        logger.info("Клиент остановлен.")

if __name__ == "__main__":
    asyncio.run(main())