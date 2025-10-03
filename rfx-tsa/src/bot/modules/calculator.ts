import type { Telegraf, Context } from "telegraf";
import { calcCost } from "../../clients/refee.js";

export function setupCalculator(bot: Telegraf<Context>) {
  bot.command("calculate", async (ctx) => {
    const args = (ctx.message as any).text.split(/\s+/).slice(1).join(" ");
    const targets = args.split(/[ ,\n\t]+/).filter(Boolean).slice(0, 20);
    if (targets.length === 0) {
      await ctx.reply("Usage: /calculate <address1,address2,... up to 20>");
      return;
    }
    const res = await calcCost(targets);
    await ctx.reply(JSON.stringify(res));
  });
}
