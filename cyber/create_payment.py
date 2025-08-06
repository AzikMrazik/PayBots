from aiogram import Bot, types, Router, F
from aiogram.fsm.context import FSMContext
import logging
import config
import aiohttp
import aiosqlite
import re

router = Router()

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/cyb_")) 
async def create_payment(msg: types.Message | types.CallbackQuery, bot: Bot, state: FSMContext, amt: str = None):
    chat_id = msg.chat.id
    amt = msg.text.split("_")[1]
    loading_msg = await bot.send_message(chat_id, "⌛Ожидаем реквизиты...")
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{config.BASE_URL}/api/v1/ast/request",
                                headers={"Authorization": f"{config.API_TOKEN}"},
                                json={"sum": amt,
                                        "payment_method": "ccard",
                                        "callback_url": f"{config.DOMAIN}/cyber/{chat_id}"}) as resp:
            try:
                data = await resp.json()
                logging.info(f"Answer: {data}")
            except:
                try:
                    data = await resp.text()
                    logging.error(f"Answer: {data}")
                except Exception as e:
                    logging.error(f"Error reading response: {e}")
                finally:
                    await msg.answer("⚰️Cyber-Money отправил труп!")
                    await loading_msg.delete()
                    return
            await loading_msg.delete()
            error = data.get("error")
            if error == "false" or error is None or error == "False" or error == False:
                data = data.get("request")
                order_id = data.get("request_id")
                card = data.get("num")
                card = re.sub(r'\s+', '', card)
                logging.info(f"{type(card[6])}: {card[6]}")
                name = await check_name(card[6])
                amt = data.get("sum")
                await bot.send_message(chat_id, f"""
📄Создана заявка на оплату!

💳Номер карты для оплаты: <code>{card}</code>
💰Сумма платежа: <code>{amt}</code> рублей

🕑Время на оплату: 25 мин.
""")
                await bot.send_message(chat_id, f"🏦Банк: {name}")
                await bot.send_message(chat_id, f"Заявка №<code>{order_id}</code>")
                return
            else:
                try:
                    error = data.get("message")
                    await msg.answer(f"⚰️Cyber-Money отправил труп!\nОшибка: {error}")
                    return
                except:
                    error = data.get("request")
                    if error == "no_requisites":
                        await msg.answer(f"⛔Нет реквизитов!")
                        return
                    else:
                        await msg.answer(f"⚰️Cyber-Money отправил труп!\nОшибка: {error}")
                        return

async def check_name(bin):
    async with aiosqlite.connect("bins.db") as db:
        cursor = await db.execute(
            "SELECT bank_name FROM bins WHERE bin = ?", 
            (bin,)
        )
        result = await cursor.fetchone()
        if result:
            return result[0]
        else:
            return "Неизвестный банк"
