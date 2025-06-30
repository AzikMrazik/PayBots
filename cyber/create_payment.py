from aiogram import Bot, types, Router, F
from aiogram.fsm.context import FSMContext
import logging
import config
import aiohttp

router = Router()


async def payment_kb(order_id, amount):
    keyboard = [
        [types.InlineKeyboardButton(text="✅Оплчачено", callback_data=f"order_paid_{order_id}")],
        [types.InlineKeyboardButton(text="⛔Отмена", callback_data=f"order_cancel_{order_id}"),
         types.InlineKeyboardButton(text="♻️Пересоздать", callback_data=f"order_recreate_{order_id}_{amount}")]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/cyb_")) 
async def create_payment(message: types.Message | types.CallbackQuery, bot: Bot, state: FSMContext, amount: str = None):
    chat_id = message.chat.id
    amount = message.text.split("_")[1]
    msg = await bot.send_message(chat_id, "⌛Ожидаем реквизиты...")
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{config.BASE_URL}/api/v1/ast/request",
                                headers={"Authorization": f"{config.API_TOKEN}"},
                                params={"sum": amount,
                                        "payment_method": "ccard",
                                        "callback_url": f"{config.DOMAIN}/cyber/{chat_id}"}) as response:
            try:
                data = await response.json()
                logging.info(f"Answer: {data}")
            except:
                try:
                    data = await response.text()
                    logging.error(f"Answer: {data}")
                except Exception as f:
                    logging.error(f"Error occurred while reading response: {f}")
                finally:
                    await message.answer("⚰️Cyber-Money отправил труп!")
                    msg.delete()
                    return
            msg.delete()
            error = data.get("error")
            if error == "false" or error is None:
                data = data.get("request")
                order_id = data.get("request_id")
                card = data.get("num")
                amount = data.get("sum")
                await bot.send_message(chat_id, f"""
📄Создана заявка на оплату!

💳Номер карты для оплаты: <code>{card}</code>
💰Сумма платежа: <code>{amount}</code> рублей

🕑Время на оплату: 30 мин.
""", reply_markup=payment_kb(order_id, amount))
                return
            else:
                data = data.get("request")
                error = data.get("message")
                await message.answer(f"⚰️Cyber-Money отправил труп!\nОшибка: {error}")
                return
            
@router.callback_query(F.data.startswith("order"))
async def handle_order_callback(callback_query: types.CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    data = callback_query.data.split("_")
    action = data[1]
    order_id = data[2]
    if action == "paid":
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{config.BASE_URL}/api/v1/ast/{order_id}/confirm", headers={"Authorization": f"{config.API_TOKEN}"}) as response:
                pass
        return
    elif action == "cancel":
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{config.BASE_URL}/api/v1/ast/{order_id}/cancel", headers={"Authorization": f"{config.API_TOKEN}"}) as response:
                pass
        return
    elif action == "recreate":
        amount = data[3]
        await create_payment(callback_query, bot, state, amount)



