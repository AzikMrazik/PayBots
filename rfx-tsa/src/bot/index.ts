import { Telegraf } from "telegraf";
import { config } from "../utils/config.js";
import { logger } from "../utils/logger.js";
import { createBot } from "./setup.js";
import { getDb } from "../db/connection.js";

async function main() {
  if (!config.telegramToken) {
    logger.error("TELEGRAM_BOT_TOKEN is missing");
    process.exit(1);
  }
  if (!config.refeeToken) {
    logger.warn("REFEE_API_TOKEN not set; API calls will fail until provided");
  }
  await getDb();
  const bot = new Telegraf(config.telegramToken);
  await createBot(bot);
  await bot.launch();
  logger.info("Bot started");
  process.once("SIGINT", () => bot.stop("SIGINT"));
  process.once("SIGTERM", () => bot.stop("SIGTERM"));
}

main().catch((err) => {
  logger.error({ err }, "Fatal error");
  process.exit(1);
});
