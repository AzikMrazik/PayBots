import { getDb } from "./connection.js";

export async function recordOrder(userId: string, kind: "energy"|"bandwidth", days: string, volume: number, target: string, externalId: string | null) {
  const db = await getDb();
  db.prepare("INSERT INTO orders (user_id, kind, days, volume, target, external_id) VALUES (?, ?, ?, ?, ?, ?)").run(userId, kind, days, volume, target, externalId);
}
