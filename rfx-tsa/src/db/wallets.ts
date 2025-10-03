import { getDb } from "./connection.js";

export async function addWallet(userId: string, address: string) {
  const db = await getDb();
  db.prepare("INSERT OR IGNORE INTO wallets (user_id, address) VALUES (?, ?)").run(userId, address);
}

export async function removeWallet(userId: string, address: string) {
  const db = await getDb();
  db.prepare("DELETE FROM wallets WHERE user_id = ? AND address = ?").run(userId, address);
}

export async function setFavoriteWallet(userId: string, address: string) {
  const db = await getDb();
  const tx = db.transaction(() => {
    db.prepare("UPDATE wallets SET is_favorite = 0 WHERE user_id = ?").run(userId);
    db.prepare("UPDATE wallets SET is_favorite = 1 WHERE user_id = ? AND address = ?").run(userId, address);
  });
  tx();
}

export async function listWallets(userId: string) {
  const db = await getDb();
  return db.prepare("SELECT address, is_favorite FROM wallets WHERE user_id = ? ORDER BY is_favorite DESC, created_at DESC").all(userId) as { address: string; is_favorite: 0|1 }[];
}

export async function getFavoriteWallet(userId: string) {
  const db = await getDb();
  const row = db.prepare("SELECT address FROM wallets WHERE user_id = ? AND is_favorite = 1").get(userId) as { address: string } | undefined;
  return row?.address ?? null;
}
