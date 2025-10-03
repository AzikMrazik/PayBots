import { getDb } from "./connection.js";

export async function ensureUser(userId: string) {
  const db = await getDb();
  db.prepare("INSERT OR IGNORE INTO users (id) VALUES (?)").run(userId);
}

export async function getUserById(userId: string) {
  const db = await getDb();
  await ensureUser(userId);
  const row = db.prepare("SELECT id, balance FROM users WHERE id = ?").get(userId) as { id: string; balance: number } | undefined;
  return row ?? null;
}

export async function incrementUserBalance(userId: string, amount: number) {
  const db = await getDb();
  await ensureUser(userId);
  db.prepare("UPDATE users SET balance = balance + ? WHERE id = ?").run(amount, userId);
}

export async function decrementUserBalance(userId: string, amount: number) {
  const db = await getDb();
  await ensureUser(userId);
  db.prepare("UPDATE users SET balance = MAX(0, balance - ?) WHERE id = ?").run(amount, userId);
}
