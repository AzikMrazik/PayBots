import type { Telegraf, Context } from "telegraf";
import { setupBasicCommands } from "./modules/basic.js";
import { setupBalanceCommands } from "./modules/balance.js";
import { setupWallets } from "./modules/wallets.js";
import { setupPurchases } from "./modules/purchases.js";
import { setupCalculator } from "./modules/calculator.js";

export async function createBot(bot: Telegraf<Context>) {
  setupBasicCommands(bot);
  setupBalanceCommands(bot);
  setupWallets(bot);
  setupPurchases(bot);
  setupCalculator(bot);
}
