import Database from "better-sqlite3";
import { config } from "../utils/config.js";
import { logger } from "../utils/logger.js";

let db: Database.Database | null = null;

export async function getDb() {
  if (db) return db;
  const filename = config.databaseUrl.replace(/^file:/, "");
  db = new Database(filename);
  db.pragma("journal_mode = WAL");
  migrate(db);
  return db;
}

function migrate(db: Database.Database) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      balance INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS wallets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      address TEXT NOT NULL,
      is_favorite INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, address)
    );
    CREATE TABLE IF NOT EXISTS orders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      kind TEXT NOT NULL,
      days TEXT NOT NULL,
      volume INTEGER NOT NULL,
      target TEXT NOT NULL,
      external_id TEXT,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
  `);
  logger.info("DB migrations applied");
}
