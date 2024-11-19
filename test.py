import asyncio
import logging
from pyrogram import Client, filters

logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (DEBUG для подробных логов)
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

@app.on_message()
async def forward_message(client, message):
    try:
        # Проверяем, что сообщение пришло из нужной группы
        if message.chat.id == source_chat_id:
            await client.forward_messages(chat_id=target_channel_id, from_chat_id=message.chat.id, message_ids=message.id)
            logger.info(f"Сообщение переслано: {message.text}")
        else:
            logger.debug(f"Сообщение из другого чата: {message.chat.id}")
    except Exception as e:
        logger.error(f"Ошибка при пересылке сообщения: {e}")

async def main():
    try:
        if not app.is_connected:
            await app.start()
        logger.info("Клиент запущен и готов к работе.")
        await asyncio.Event().wait()  # Ожидание
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
    finally:
        if app.is_connected:
            await app.stop()
            logger.info("Клиент остановлен корректно.")

if __name__ == "__main__":
    asyncio.run(main())
