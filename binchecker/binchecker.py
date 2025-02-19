import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from BINs import bin_database
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def extract_bins(text):
    numbers = re.findall(r"\b\d{6,}", text)  # Находим последовательности от 6 цифр
    return {n[:6] for n in numbers if len(n) >= 6}  # Берем первые 6 цифр

@dp.message(Command("ping"))
async def start_command(message: Message):
    msg = await message.answer("🗑️BinChecker на связи✅")
    await asyncio.sleep(5)
    await msg.delete()

@dp.message()
async def handle_message(message: types.Message):
    bins = extract_bins(message.text)
    if not bins:
        return
    
    results = []
    for bin_code in bins:
        bank = bin_database.get(bin_code, 'Неизвестный банк')
        results.append(f"{bank}")
    
    response = "\n".join(results)
    await message.reply(response)

if __name__ == '__main__':
    import asyncio
    asyncio.run(dp.start_polling(bot))