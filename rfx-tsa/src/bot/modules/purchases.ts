import type { Telegraf, Context } from "telegraf";
import { buyBandwidth, buyEnergy, RefeeError } from "../../clients/refee.js";
import { recordOrder } from "../../db/orders.js";
import { getUserById, decrementUserBalance } from "../../db/users.js";

function parseArgs(text: string) {
  const parts = text.split(/\s+/).slice(1);
  const params: any = {};
  for (const p of parts) {
    const [k,v] = p.split("=");
    if (k && v) params[k] = v;
  }
  return params;
}

const ENERGY_DAYS = new Set(["1h", "1d", "3d", "7d", "14d"]);
const BANDWIDTH_DAYS = new Set(["1h", "3d", "7d", "14d"]);

export function setupPurchases(bot: Telegraf<Context>) {
  bot.command("buyenergy", async (ctx) => {
    const userId = ctx.from?.id?.toString() ?? "";
    const params = parseArgs((ctx.message as any).text);
    const days = params.days;
    const volume = Number(params.volume);
    const target = params.target;
    if (!days || !volume || !target) {
      await ctx.reply("Usage: /buyenergy days=1h|1d|3d|7d|14d volume=32000-2000000 target=ADDRESS");
      return;
    }
    if (!ENERGY_DAYS.has(days)) {
      await ctx.reply("Invalid days. Use one of 1h,1d,3d,7d,14d");
      return;
    }
    if (volume < 32000 || volume > 2000000) {
      await ctx.reply("Invalid volume. Range: 32000 - 2000000");
      return;
    }
    const user = await getUserById(userId);
    if (!user) return;
    if (user.balance < volume) {
      await ctx.reply("Insufficient balance. Use /topup.");
      return;
    }
    try {
      const res = await buyEnergy({ days, volume, target });
      await decrementUserBalance(userId, volume);
      await recordOrder(userId, "energy", days, volume, target, res.orderId ?? null);
      await ctx.reply("Energy purchased.");
    } catch (e: any) {
      if (e instanceof RefeeError) {
        if (e.status === 422) {
          await ctx.reply("Request rejected (possibly inactive wallet or invalid params).");
        } else if (e.status === 403) {
          await ctx.reply("Auth failed. Please contact admin.");
        } else {
          await ctx.reply(`Upstream error ${e.status}: ${e.message}`);
        }
      } else {
        await ctx.reply("Unexpected error during purchase.");
      }
    }
  });

  bot.command("buybandwidth", async (ctx) => {
    const userId = ctx.from?.id?.toString() ?? "";
    const params = parseArgs((ctx.message as any).text);
    const days = params.days;
    const volume = Number(params.volume);
    const target = params.target;
    if (!days || !volume || !target) {
      await ctx.reply("Usage: /buybandwidth days=1h|3d|7d|14d volume=1000-2000000 target=ADDRESS");
      return;
    }
    if (!BANDWIDTH_DAYS.has(days)) {
      await ctx.reply("Invalid days. Use one of 1h,3d,7d,14d");
      return;
    }
    if (volume < 1000 || volume > 2000000) {
      await ctx.reply("Invalid volume. Range: 1000 - 2000000");
      return;
    }
    const user = await getUserById(userId);
    if (!user) return;
    if (user.balance < volume) {
      await ctx.reply("Insufficient balance. Use /topup.");
      return;
    }
    try {
      const res = await buyBandwidth({ days, volume, target });
      await decrementUserBalance(userId, volume);
      await recordOrder(userId, "bandwidth", days, volume, target, res.orderId ?? null);
      await ctx.reply("Bandwidth purchased.");
    } catch (e: any) {
      if (e instanceof RefeeError) {
        if (e.status === 422) {
          await ctx.reply("Request rejected (possibly inactive wallet or invalid params).");
        } else if (e.status === 403) {
          await ctx.reply("Auth failed. Please contact admin.");
        } else {
          await ctx.reply(`Upstream error ${e.status}: ${e.message}`);
        }
      } else {
        await ctx.reply("Unexpected error during purchase.");
      }
    }
  });
}
