import asyncio
from pyrogram import Client, filters

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
        await client.forward_messages(chat_id=target_channel_id, from_chat_id=message.chat.id, message_ids=message.id)
        print(f"Сообщение переслано: {message.text}")
    except Exception as e:
        print(f"Ошибка при пересылке: {e}")

async def main():
    await app.start()
    print("Клиент запущен. Ожидание сообщений...")
    # Используем asyncio.Event вместо idle()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())