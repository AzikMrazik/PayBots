from aiogram import Bot, types, Router, F
import logging
import config
import aiohttp
import aiosqlite
import re
from datetime import datetime

router = Router()

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/card_")) 
@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/amore_")) 
async def create_payment(msg: types.Message | types.CallbackQuery, bot: Bot):
    order_id = datetime.now().strftime("%d%m%H%M")
    chat_id = msg.chat.id
    amount = msg.text.split("_")[1]
    try:
        pay_type = msg.text.split("_")[2]
        pay_type = pay_type.replace(".", "_")
        pay_types = "payment_gateway"      
    except:
        pay_types = "currency"
        pay_type = "rub"
    loading_msg = await bot.send_message(chat_id, "⌛Ожидаем реквизиты...")
    json = {"external_id": order_id,
            "amount": amount,
            f"{pay_types}": f"{pay_type}",
            "merchant_id": f"{config.MERCHANT_ID}",
            "callback_url": f"https://{config.DOMAIN}/amore/{chat_id}"}
    if msg.text.split("_")[0] == "/card":
        json["payment_detail_type"] = "card"
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{config.BASE_URL}/api/h2h/order",
                                headers={"Accept": "application/json", "Access-Token": f"{config.API_TOKEN}"},
                                json=json) as resp:
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
                    await msg.answer("⚰️Amore Pay отправил труп!")
                    await loading_msg.delete()
                    return
            await loading_msg.delete()
            if data.get("success") == True or data.get("success") == "true":
                data = data.get("data")
                payment_detail = data.get("payment_detail")
                order_id = data.get("order_id")
                owner_name = payment_detail.get("initials")
                card = payment_detail.get("detail")
                card = re.sub(r'\s+', '', card)
                logging.info(f"{type(card[:6])}: {card[:6]}")
                name = await check_name(card[:6])
                await bot.send_message(chat_id, f"""
📄Создана заявка на оплату!

💳Номер карты для оплаты: <code>{card}</code>
💰Сумма платежа: <code>{amount}</code> рублей

🕑Время на оплату: 25 мин.
""")
                await bot.send_message(chat_id, f"🏦Банк: {name}")           
                await bot.send_message(chat_id, f"🙍‍♂️Получатель: {owner_name}")
                await bot.send_message(chat_id, f"Заявка №<code>{order_id}</code>")
                return
            else:
                try:
                    error = data.get("message")
                    if error:
                        await msg.answer(f"⚰️Amore Pay отправил труп!\nОшибка: {error}")
                        return
                    else:
                        error = data.get("message")
                        if error == "no_requisites":
                            await msg.answer(f"⛔Нет реквизитов!")
                        else:
                            await msg.answer(f"⚰️Amore Pay отправил труп!\nОшибка: {error}") 
                except:
                    await msg.answer(f"⚰️Amore Pay отправил труп!\nОшибка: {data}")
                    pass

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
