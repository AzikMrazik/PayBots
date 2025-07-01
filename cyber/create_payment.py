from aiogram import Bot, types, Router, F
from aiogram.fsm.context import FSMContext
import logging
import config
import aiohttp

router = Router()


def payment_kb(order_id, amount, msg):
    kb = [
        [types.InlineKeyboardButton(text="✅Оплачено", callback_data=f"order_paid_{order_id}_{msg}")],
        [types.InlineKeyboardButton(text="⛔Отмена", callback_data=f"order_cancel_{order_id}_{msg}"),
         types.InlineKeyboardButton(text="♻️Пересоздать", callback_data=f"order_recreate_{order_id}_{msg}_{amount}")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

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
                amt = data.get("sum")
                msg = await bot.send_message(chat_id, f"""
📄Создана заявка на оплату!

💳Номер карты для оплаты: <code>{card}</code>
💰Сумма платежа: <code>{amt}</code> рублей

🕑Время на оплату: 30 мин.
""")
                await bot.send_message(chat_id, f"Заявка №<code>{order_id}</code>", reply_markup=payment_kb(order_id, amt, msg.message_id))
                return
            else:
                data = data.get("request")
                error = data.get("message")
                await msg.answer(f"⚰️Cyber-Money отправил труп!\nОшибка: {error}")
                return
            
@router.callback_query(F.data.startswith("order"))
async def handle_order_callback(callback_query: types.CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    data = callback_query.data.split("_")
    action = data[1]
    order_id = data[2]
    msg_id = int(data[3]) 
    if action == "paid":
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{config.BASE_URL}/api/v1/ast/{order_id}/confirm", headers={"Authorization": f"{config.API_TOKEN}"}) as response:
                pass
            await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=msg_id, text="✅Оплата подтверждена!")
            logging.info(f"Order {order_id} confirmed")   
        return
    elif action == "cancel":
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{config.BASE_URL}/api/v1/ast/{order_id}/cancel", headers={"Authorization": f"{config.API_TOKEN}"}) as response:
                pass
            await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=msg_id, text="⛔Оплата отменена!")
            logging.info(f"Order {order_id} cancelled")
        return
    elif action == "recreate":
        amount = data[4]
        logging.info(f"Recreating order {order_id} with amount {amount}")
        await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=msg_id, text="♻️Пересоздание заказа...")
        await create_payment(callback_query, bot, state, amount)



