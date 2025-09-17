
from aiogram import Router, F
from aiogram.types import Message
import config
import aiohttp

router = Router()

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/types_"))
async def types_command(msg: Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{config.BASE_URL}/api/payment-gateways",
                                headers={"Accept": "application/json", "Access-Token": f"{config.API_TOKEN}"}) as resp:
            data = await resp.json()
            data = data.get("data")
            for i in range(len(data)):
                if data[i].get('currency') != "rub":
                    continue
                name = data[i].get('name')
                code = data[i].get('code')
                min_limit = data[i].get('min_limit')
                max_limit = data[i].get('max_limit')
                reserve_time = data[i].get('reserve_time')
                detail_types = data[i].get('detail_types')
                types_list = []
                if "card" in detail_types:
                    types_list.append("карты")
                if "sbp" in detail_types:
                    types_list.append("СБП")
                if "account" in detail_types:
                    types_list.append("по номеру счёта")
                commission = data[i].get('service_commission_rate')
                rate = data[i].get('conversion_price')
                await msg.answer(f"""
                Метод: {name} 
                Код: {code}

                Лимиты: {min_limit} - {max_limit}
                Время на оплату: {reserve_time}
                Типы: {', '.join(types_list)}

                Комиссия: {commission}
                Курс: {rate}
                """)

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/check_"))
async def check_command(msg: Message):
    order_id = msg.text.split("_")[1]
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{config.BASE_URL}/api/h2h/order/{order_id}",
                                headers={"Accept": "application/json", "Access-Token": f"{config.API_TOKEN}"}) as resp:
            data = await resp.json()
            data = data.get('data')
            order_id = data.get('external_id')
            amount = data.get('amount')
            status = data.get('status')
            if status == "pending":
                sign = "⚠️"
                status = "ожидает оплаты"
            elif status == "success":
                sign = "✅"
                status = "успешно оплачен"
            elif status == "fail":
                sign = "⛔"
                status = "отменен"
            await msg.answer(f"{sign}Заказ №{order_id} на сумму {amount}₽ {status}!")

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.startswith("/cancel_"))
async def check_command(msg: Message):
    order_id = msg.text.split("_")[1]
    async with aiohttp.ClientSession() as session:
        async with session.patch(f"{config.BASE_URL}/api/h2h/order/{order_id}/cancel",
                                headers={"Accept": "application/json", "Access-Token": f"{config.API_TOKEN}"}) as resp:
                                pass





