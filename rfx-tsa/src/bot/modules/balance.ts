import type { Telegraf, Context } from "telegraf";
import { getRefillAddress } from "../../clients/refee.js";
import { ensureUser, getUserById } from "../../db/users.js";

export function setupBalanceCommands(bot: Telegraf<Context>) {
  bot.command("balance", async (ctx) => {
    const userId = ctx.from?.id?.toString() ?? "";
    await ensureUser(userId);
    const user = await getUserById(userId);
    await ctx.reply(`Your balance: ${user?.balance ?? 0}`);
  });
  bot.command("topup", async (ctx) => {
    const info = await getRefillAddress();
    await ctx.reply(`Send TRX to refill address: ${info.address}`);
  });
}
