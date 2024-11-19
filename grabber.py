import asyncio
import logging
import os
from dotenv import load_dotenv
from pyrogram import Client
from sqlite3 import OperationalError

load_dotenv(dotenv_path='/root/paybots/api.env')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Ваши данные
api_id = int(os.getenv('API_ID'))  # Замените на ваш API ID
api_hash = os.getenv('API_HASH') # Замените на ваш API Hash
session_name = "boter"  # Имя сессии

# ID чатов
source_chat_id = os.getenv('SOURCE_CHAT_ID') # ID группы (источник)
target_channel_id = os.getenv('SOURCE_CHANNEL_ID')  # ID канала (назначение)

print({api_id},{api_hash},{source_chat_id},{target_channel_id})


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
    except OperationalError as e:
        logger.error(f"База данных заблокирована: {e}")
        await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Ошибка при пересылке сообщения: {e}")

async def main():
    try:
        await app.start()
        logger.info("Клиент запущен и готов к работе.")
        await asyncio.Event().wait()  # Ожидание
    except OperationalError as e:
        logger.critical(f"База данных заблокирована: {e}. Перезапуск...")
    except asyncio.CancelledError:
        logger.warning("Завершение работы...")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
    finally:
        if app.is_connected:
            await app.stop()
            logger.info("Клиент остановлен корректно.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Остановка по Ctrl+C")
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
