import asyncio
import logging
import os
from dotenv import load_dotenv
from pyrogram import Client, errors
from sqlite3 import OperationalError

# Загрузка переменных окружения
load_dotenv(dotenv_path='/root/paybots/api.env')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Загрузка данных
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
session_name = "boter"

# ID чатов
source_chat_id = int(os.getenv('SOURCE_CHAT_ID'))
target_channel_id = int(os.getenv('TARGET_CHANNEL_ID'))

# ID пользователя для фильтрации
user_id_filter = int(os.getenv('USER_ID_FILTER'))

# Слова для фильтрации, загружаем из .env и разделяем на список
filter_words = os.getenv('FILTER_WORDS', '').split(',')

# Проверка данных
logger.info(f"API_ID: {api_id}, SOURCE_CHAT_ID: {source_chat_id}, TARGET_CHANNEL_ID: {target_channel_id}")
logger.info(f"Слова для фильтрации: {filter_words}")

# Инициализация клиента
app = Client(session_name, api_id=api_id, api_hash=api_hash)

async def send_message_safely(client, chat_id, text):
    """Безопасная отправка сообщения с несколькими попытками"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await client.send_message(chat_id, text)
            logger.info(f"Сообщение успешно отправлено в чат {chat_id}")
            return True
        except errors.FloodWait as e:
            logger.warning(f"Flood wait: waiting for {e.value} seconds")
            await asyncio.sleep(e.value)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения (попытка {attempt + 1}): {e}")
            await asyncio.sleep(2)  # Небольшая задержка между попытками
    
    logger.error(f"Не удалось отправить сообщение в чат {chat_id} после {max_retries} попыток")
    return False

@app.on_message()
async def forward_message(client, message):
    try:
        # Проверяем, что сообщение пришло из нужной группы
        if message.chat.id == source_chat_id:
            # Проверяем, что сообщение отправлено указанным пользователем
            if message.from_user and message.from_user.id == user_id_filter:
                # Проверка на наличие слов из фильтра
                if any(word.lower() in message.text.lower() for word in filter_words if word):
                    logger.info(f"Сообщение содержит запрещенные слова и не будет переслано: {message.text}")
                    return
                
                try:
                    # Расширенная попытка пересылки с обработкой различных сценариев
                    logger.info(f"Попытка пересылки сообщения от {message.from_user.id} из {message.chat.id} в {target_channel_id}")
                    
                    # Пытаемся переслать сообщение с расширенной обработкой ошибок
                    try:
                        await client.forward_messages(
                            chat_id=target_channel_id, 
                            from_chat_id=message.chat.id, 
                            message_ids=message.id
                        )
                        logger.info(f"Сообщение успешно переслано: {message.text}")
                    except errors.FloodWait as flood_error:
                        # Обработка флуд-контроля
                        wait_time = flood_error.value
                        logger.warning(f"Флуд-контроль. Ожидание {wait_time} секунд.")
                        await asyncio.sleep(wait_time)
                        # Повторная попытка пересылки
                        await client.forward_messages(
                            chat_id=target_channel_id, 
                            from_chat_id=message.chat.id, 
                            message_ids=message.id
                        )
                    except errors.PeerIdInvalid:
                        # Если не удается переслать, пробуем отправить как копию
                        logger.warning("Не удалось переслать. Попытка отправить как копию.")
                        await send_message_safely(client, target_channel_id, message.text)
                    except Exception as forward_error:
                        logger.error(f"Критическая ошибка при пересылке: {forward_error}")
                        # Последняя попытка - отправить текст сообщения
                        await send_message_safely(client, target_channel_id, message.text)
                
                except Exception as unexpected_error:
                    logger.error(f"Неожиданная ошибка: {unexpected_error}")
            
            else:
                logger.debug(f"Сообщение от другого пользователя: {message.from_user.id if message.from_user else 'Неизвестно'}")
        else:
            logger.debug(f"Сообщение из другого чата: {message.chat.id}")
    
    except Exception as global_error:
        logger.error(f"Глобальная ошибка при обработке сообщения: {global_error}")

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
