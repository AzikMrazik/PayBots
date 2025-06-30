import logging
import os
from datetime import datetime
from aiogram.types import Update, Message, CallbackQuery
from aiogram import Bot
import config
import keyboards
from lexicon import get_text

## Настройка логирования в файл с ротацией
def setup_file_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, "errors.log")
    
    ## Проверяем размер файла лога (в байтах)
    max_log_size = 10 * 1024 * 1024  ## 10 MB
    if os.path.exists(log_file) and os.path.getsize(log_file) > max_log_size:
        ## Создаем резервную копию и очищаем файл
        backup_file = os.path.join(log_dir, f"bot_errors_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        os.rename(log_file, backup_file)
    
    ## Настройка логгера для файла
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.ERROR)
    file_formatter = logging.Formatter(
        '%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    ## Получаем основной логгер и добавляем файловый хендлер
    logger = logging.getLogger()
    logger.addHandler(file_handler)

async def handle_all_errors(event, exception: Exception):

    ## Настраиваем файловое логирование при первом вызове
    setup_file_logging()
    
    ## Получаем информацию об обновлении
    update = getattr(event, 'update', None)
    chat_id = None

    if update and update.message:
        chat_id = update.message.chat.id
    elif update and update.callback_query:
        chat_id = update.callback_query.chat.id
    
    ## Формируем детальное сообщение об ошибке
    error_details = f"""
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
chat ID: {chat_id}
Exception Type: {type(exception).__name__}
Exception Message: {str(exception)}
Update Type: {type(update).__name__ if update else 'Unknown'}
    """
    
    ## Логируем ошибку в файл и консоль
    logging.error(error_details, exc_info=True)
    
    ## Отправляем сообщение пользователю об ошибке
    if chat_id:
        try:
            from main import bot, main_menu_handler
            
            await bot.send_message(chat_id, text=await get_text("error_occurred", chat_id), reply_markup=keyboards.error_kb())
            logging.info(f"Error message sent to chat {chat_id}")
            if update.callback_query:
                await bot.answer_callback_query(update.callback_query.id)

        except Exception as send_error:
            logging.error(f"Failed to send error message to chat {chat_id}: {send_error}")
    
    ## Отправляем уведомление администратору/технарю
    try:
        from main import bot
        admin_message = f"""
<b>Время:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
<b>Пользователь:</b> (ID: {chat_id})
<b>Тип ошибки:</b> <code>{type(exception).__name__}</code>
<b>Сообщение:</b> <code>{str(exception)}</code>
            """
        await bot.send_message(config.TECH_ID, admin_message)
    except Exception as admin_error:
        logging.error(f"Failed to send error notification to admin: {admin_error}")
    
    return True