import asyncio
import aiohttp
import logging

settings = {
    "name": "E-Pay",
    "commission": 0.3,
    "secrets": {"secret_1": {"name": "api_key", "description": "API Key for E-Pay, get in profile on e-pay.plus"}},
    "custom_order_id": True}

async def create_payment(api_key, amount=3980):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post("https://epay.com/api/create_payment",
                                    json={
                                        "amount": amount,
                                        "api_key": api_key,
                                        "merchant_order_id": "optional"}) as response:
                try:
                    data = await response.json()
                    order_id = data.get("order_id")
                    amount = data.get("amount")
                    requisites = data.get("card_number")
                    return {
                        "status": "success",
                        "order_id": order_id,
                        "amount": amount,
                        "requisites": requisites
                    }
                except:
                    data = await response.text()
                    raise Exception(f"Error in response: {data}")      
        except aiohttp.ClientError as e:
            logging.error(f"Network error while creating payment: {e}")
            return {"status": "error", "message": str(e)}                            

async def process_callback(request):
    try:
        data = await request.json()
        return True
    except Exception as e:
        logging.error(f"Error processing callback: {e}")
        return {"status": "error", "message": str(e)}
        


