import type { Telegraf, Context } from "telegraf";
import { ensureUser } from "../../db/users.js";

export function setupBasicCommands(bot: Telegraf<Context>) {
  bot.start(async (ctx) => {
    await ensureUser(ctx.from?.id?.toString() ?? "");
    await ctx.reply("Welcome to RF x TSA — Transaction Savings Assistant. Use /help for commands.");
  });
  bot.help(async (ctx) => {
    await ctx.reply([
      "/balance - Check your internal balance",
      "/topup - Get refill address to top up balance",
      "/buyenergy - Purchase energy",
      "/buybandwidth - Purchase bandwidth",
      "/wallets - Manage saved wallets",
      "/calculate - Calculate energy for transfers"
    ].join("\n"));
  });
}
