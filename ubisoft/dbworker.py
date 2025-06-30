import aiosqlite
import logging
import asyncio
import os

async def init_db():

    db_dir = "db"

    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    logging.info("Initializing database...")

    # Create the database and the chats table if it doesn't exist

    try:
        async with aiosqlite.connect(f'db/chats.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id INTEGER PRIMARY KEY,
                    chat_type TEXT DEFAULT 'private',  -- Default chat type is private
                    lang TEXT DEFAULT 'ru',  -- Default language is Russian
                    api_keys TEXT DEFAULT '[]',  -- Default api_keys is an empty list
                    systems TEXT DEFAULT '[generator, templator]'  -- Default systems is an stock systems list
                )                   
            ''')
            await db.commit()   
    except aiosqlite.Error as e:
        logging.error(f"Database initialization error: {e}")

async def get_chatinfo(chat_id: int) -> dict:
    async with aiosqlite.connect('db/chats.db') as db:
        cursor = await db.execute("SELECT * FROM chats WHERE chat_id = ?", (chat_id,))
        row = await cursor.fetchone()
        if row:
            logging.info(f"Chat {chat_id} found in the database.")
            answer = {}
            for i in range(len(row)):
                answer[cursor.description[i][0]] = row[i]
            await cursor.close()
            await db.close()
            return answer
        else:
            await add_chat(chat_id)
            return await get_chatinfo(chat_id)

async def add_chat(chat_id: int):
    if chat_id < 0:
        chat_type = 'group'
    else:
        chat_type = 'private'
    async with aiosqlite.connect('db/chats.db') as db:
        await db.execute("INSERT INTO chats (chat_id, chat_type) VALUES (?, ?)", (chat_id, chat_type))
        await db.commit()
        logging.info(f"Chat {chat_id} added to the database.")
        return {
            'chat_id': chat_id,
            'chat_type': chat_type,
        }

async def change_chatinfo(chat_id: int, **kwargs):

    if not kwargs:
        logging.warning("No chat info provided to change.")
        return
    
    fields = ', '.join(f"{key} = ?" for key in kwargs.keys())
    values = list(kwargs.values())

    async with aiosqlite.connect('db/chats.db') as db:
        await db.execute(f"UPDATE chats SET {fields} WHERE chat_id = ?", (*values, chat_id))
        await db.commit()
        logging.info(f"Chat {chat_id} info updated: {kwargs}")
