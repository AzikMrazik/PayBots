import pytest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

from handlers.balance import cb_balance
from handlers.purchase import cb_refill_amount


class DummyBot:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher


class DummyCall:
    def __init__(self, data: str, user_id: int = 1):
        self.data = data
        self.from_user = SimpleNamespace(id=user_id)
        self.message = SimpleNamespace(
            bot=DummyBot(SimpleNamespace()),
            edit_text=AsyncMock(),
        )

    async def answer(self, *args, **kwargs):
        pass


@pytest.mark.asyncio
async def test_cb_balance_shows_balance():
    db = AsyncMock()
    db.get_balance.return_value = Decimal("15")
    dispatcher = {"db": db}
    call = DummyCall("menu:balance")
    call.message.bot.dispatcher = dispatcher  # type: ignore
    await cb_balance(call)
    call.message.edit_text.assert_called()


@pytest.mark.asyncio
async def test_cb_refill_amount_updates_balance():
    db = AsyncMock()
    db.add_balance.return_value = Decimal("20")
    dispatcher = {"db": db}
    call = DummyCall("refill:amount:5")
    call.message.bot.dispatcher = dispatcher  # type: ignore
    await cb_refill_amount(call, AsyncMock())
    call.message.edit_text.assert_called()
