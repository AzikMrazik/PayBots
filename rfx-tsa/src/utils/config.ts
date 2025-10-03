import dotenv from "dotenv";
dotenv.config();
export const config = {
  refeeApiBaseUrl: "https://api.refee.bot",
  refeeToken: process.env.REFEE_API_TOKEN ?? "",
  telegramToken: process.env.TELEGRAM_BOT_TOKEN ?? "",
  databaseUrl: process.env.DATABASE_URL ?? "file:./data.db",
  logLevel: (process.env.LOG_LEVEL ?? "info") as "debug"|"info"|"warn"|"error"
};
