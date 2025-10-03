import asyncio
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import AsyncIterator, List, Optional, Tuple

import aiosqlite


class Database:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    async def initialize(self) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    balance TEXT NOT NULL DEFAULT '0',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS wallets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    wallet_address TEXT NOT NULL,
                    label TEXT,
                    UNIQUE(user_id, wallet_address),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
                """
            )
            await db.commit()

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[aiosqlite.Connection]:
        db = await aiosqlite.connect(self._db_path)
        try:
            db.row_factory = aiosqlite.Row
            yield db
        finally:
            await db.close()

    async def ensure_user(self, user_id: int) -> None:
        async with self.connection() as db:
            await db.execute(
                "INSERT OR IGNORE INTO users(user_id, balance) VALUES(?, '0')",
                (user_id,),
            )
            await db.commit()

    async def get_balance(self, user_id: int) -> Decimal:
        await self.ensure_user(user_id)
        async with self.connection() as db:
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                if not row:
                    return Decimal("0")
                return Decimal(row["balance"])

    async def add_balance(self, user_id: int, amount: Decimal) -> Decimal:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        await self.ensure_user(user_id)
        async with self.connection() as db:
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                current = Decimal(row["balance"]) if row else Decimal("0")
            new_balance = current + amount
            await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (str(new_balance), user_id))
            await db.commit()
            return new_balance

    async def subtract_balance(self, user_id: int, amount: Decimal) -> Decimal:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        await self.ensure_user(user_id)
        async with self.connection() as db:
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cur:
                row = await cur.fetchone()
                current = Decimal(row["balance"]) if row else Decimal("0")
            if current < amount:
                raise ValueError("Недостаточно средств на балансе")
            new_balance = current - amount
            await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (str(new_balance), user_id))
            await db.commit()
            return new_balance

    async def add_wallet(self, user_id: int, address: str, label: Optional[str]) -> None:
        await self.ensure_user(user_id)
        async with self.connection() as db:
            await db.execute(
                "INSERT OR IGNORE INTO wallets(user_id, wallet_address, label) VALUES(?, ?, ?)",
                (user_id, address, label),
            )
            await db.commit()

    async def list_wallets(self, user_id: int) -> List[Tuple[int, str, Optional[str]]]:
        async with self.connection() as db:
            async with db.execute(
                "SELECT id, wallet_address, label FROM wallets WHERE user_id = ? ORDER BY id ASC",
                (user_id,),
            ) as cur:
                rows = await cur.fetchall()
                return [(row["id"], row["wallet_address"], row["label"]) for row in rows]

