import asyncio
from aiohttp import ClientSession
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.formatting import *
from config import BASE_URL, MERCHANT_ID, MERCHANT_TOKEN, DOMAIN
from datetime import datetime
from urllib.parse import urljoin

router = Router()

class PaymentStates(StatesGroup):
    WAITING_AMOUNT = State()

def back_kb():
    keyboard = [
        [InlineKeyboardButton(text="Назад в меню", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(F.data == 'create_payment')
async def how_many(callback_query: CallbackQuery, bot: Bot, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.answer("Введите сумму платежа:", reply_markup=back_kb())
    await state.set_state(PaymentStates.WAITING_AMOUNT)

@router.message(PaymentStates.WAITING_AMOUNT)
async def create_payment(message: Message,  state: FSMContext):
    await state.clear()
    try:
        amount = int(message.text)
        if amount < 1000:
            await message.answer("Доступная сумма: 1000 - 10.000 RUB!")
            await message.answer("Отправьте новое значение:", reply_markup=back_kb())
            return   
    except:
        await message.answer("Вы отправили не числовое значение!")
        await message.answer("Отправьте новое значение:", reply_markup=back_kb())
        return
    else:
        msg = await message.reply("⌛️Ожидаем реквизиты...")
        order = await sendpost(amount, message.from_user.id)
        await msg.delete()
        for i in order:
            await message.answer(i)
        await message.answer("Введите сумму для следующего платежа:", reply_markup=back_kb())
        await state.set_state(PaymentStates.WAITING_AMOUNT)
    

async def sendpost(amount, chat_id):
    order_id = datetime.now().strftime("%d%m%H%M%S")
    async with ClientSession() as session:
        # Normalize BASE_URL and DOMAIN to ensure single scheme
        base = BASE_URL if BASE_URL.startswith(("http://", "https://")) else f"https://{BASE_URL}"
        endpoint = urljoin(base.rstrip("/") + "/", "api/v1/createOrderMerchants")
        domain_base = DOMAIN if DOMAIN.startswith(("http://", "https://")) else f"https://{DOMAIN}"
        callback_url = urljoin(domain_base.rstrip("/") + "/", f"corkpay/{chat_id}")

        async with session.post(
            endpoint,
            json={
                    "ip": order_id,
                    "merchant_id": int(MERCHANT_ID),
                    "external_uui": order_id,
                    "amount": str(amount),
                    "payment_method": "P2P_CARD",
                    "api_key": MERCHANT_TOKEN,
                    "callback_url": callback_url
                }
        ) as response:
            try:
                data = await response.json()
                print(data, flush=True)
            except:
                data = await response.text()
                print(data, flush=True)
                return ("⚰️CorkPay отправил труп!", f"{data}", "Отправьте сообщение выше кодеру!")
            else:
                success = data['status']
                if not success:
                    return ("⚰️CorkPay отправил труп!", f"{data}", "Отправьте сообщение выше кодеру!")
                order = data['order']
                await sendpost2(order)

async def sendpost2(order, counter = 1):
    async with ClientSession() as session:
        base = BASE_URL if BASE_URL.startswith(("http://", "https://")) else f"https://{BASE_URL}"
        endpoint = urljoin(base.rstrip("/") + "/", "api/v1/get-merchant-order")
        async with session.post(
            endpoint,
            json={
                "order": order,
                "merchant_id": int(MERCHANT_ID),
                "api_key": MERCHANT_TOKEN
            }
        ) as response:
            try:
                data = await response.json()
                print(data, flush=True)
            except:
                data = await response.text()
                print(data, flush=True)
                return ("⚰️CorkPay отправил труп!", f"{data}", "Отправьте сообщение выше кодеру!")
            else:
                success = data['status']
                if not success:
                    return ("⚰️CorkPay отправил труп!", f"{data}", "Отправьте сообщение выше кодеру!")
                order = data['order']
                status = order['status']
                if status == "CREATE":
                    if counter < 60:
                        counter += 5
                        await asyncio.sleep(counter)
                        return await sendpost2(order, counter)
                    else:
                        return ("⛔Нет реквизитов!")
                elif status != "WAIT":
                    return ("⚰️CorkPay отправил труп!", f"{data}", "Отправьте сообщение выше кодеру!")
                else:
                    payment = data['payment']
                    details = payment['details']
                    bank = payment['bank']
                    price = data['price']
                    amount = price['buyer_paid']
                    return (f"📄 Создана заявка: №<code>{order}</code>\n\n💳 Номер для оплаты: <code>{details}</code>\n💰Сумма платежа: <code>{amount}</code> рублей\n\n🕑 Время на оплату: 10 мин.", F"🏦Банк: {bank}")
                    




