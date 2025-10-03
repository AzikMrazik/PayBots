import pytest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

from handlers.balance import cmd_balance, cmd_refill
from handlers.purchase import cmd_buy_energy


class DummyBot:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher


class DummyMessage:
    def __init__(self, text: str, user_id: int = 1):
        self.text = text
        self.from_user = SimpleNamespace(id=user_id)
        self.bot = DummyBot(SimpleNamespace())
        self._answers = []

    async def answer(self, text: str):
        self._answers.append(text)


@pytest.mark.asyncio
async def test_refill_and_balance():
    db = AsyncMock()
    db.add_balance.return_value = Decimal("10")
    db.get_balance.return_value = Decimal("10")
    dispatcher = {"db": db}
    msg = DummyMessage("/refill 10")
    msg.bot.dispatcher = dispatcher  # type: ignore
    await cmd_refill(msg)
    assert any("Текущий баланс" in s for s in msg._answers)

    msg2 = DummyMessage("/balance")
    msg2.bot.dispatcher = dispatcher  # type: ignore
    await cmd_balance(msg2)
    assert any("Ваш баланс" in s for s in msg2._answers)


@pytest.mark.asyncio
async def test_buy_energy_insufficient():
    db = AsyncMock()
    api = AsyncMock()
    api.precount_order.return_value = {"priceUSDT": "5"}
    db.subtract_balance.side_effect = Exception("Недостаточно средств")
    dispatcher = {"db": db, "api": api}
    msg = DummyMessage("/buyenergy TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf 100")
    msg.bot.dispatcher = dispatcher  # type: ignore
    await cmd_buy_energy(msg)
    assert any("Оплата невозможна" in s for s in msg._answers)

