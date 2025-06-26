import aiosqlite
import logging
import asyncio
import os

async def init_db():

    db_dir = "db"

    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    logging.info("Initializing database...")

    # Create the database and the users table if it doesn't exist

    try:
        async with aiosqlite.connect(f'db/users.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    lang TEXT DEFAULT 'ru'  -- Default language is Russian
                )                   
            ''')
    except aiosqlite.Error as e:
        logging.error(f"Database initialization error: {e}")

async def get_userinfo(user_id: int) -> dict:
    async with aiosqlite.connect('db/users.db') as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            logging.info(f"User {user_id} found in the database.")
            await cursor.close()
            await db.close()
            # Return user info as a dictionary
            # Assuming the table has columns: user_id, lang
            # Adjust the keys based on your actual table structure
            return {
                'user_id': row[0],
                'lang': row[1]
            }  
        else:
            await add_user(user_id)

async def add_user(user_id: int):
    async with aiosqlite.connect('db/users.db') as db:
        await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()
        logging.info(f"User {user_id} added to the database.")
        return {
            'user_id': user_id,
            'lang': 'ru'  # Default language is Russian
        }

async def change_userinfo(user_id: int, **kwargs):

    if not kwargs:
        logging.warning("No user info provided to change.")
        return
    
    fields = ', '.join(f"{key} = ?" for key in kwargs.keys())
    values = list(kwargs.values())

    async with aiosqlite.connect('db/users.db') as db:
        await db.execute(f"UPDATE users SET {fields} WHERE user_id = ?", (*values, user_id))
        await db.commit()
        logging.info(f"User {user_id} info updated: {kwargs}")
