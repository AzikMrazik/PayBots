import type { Telegraf, Context } from "telegraf";
import { listWallets, addWallet, removeWallet, setFavoriteWallet } from "../../db/wallets.js";

export function setupWallets(bot: Telegraf<Context>) {
  bot.command("wallets", async (ctx) => {
    const args = (ctx.message as any).text.split(/\s+/).slice(1);
    const sub = (args[0] ?? "list").toLowerCase();
    const userId = ctx.from?.id?.toString() ?? "";
    if (!userId) return;
    if (sub === "add") {
      const address = args[1];
      if (!address) {
        await ctx.reply("Usage: /wallets add <TRON_ADDRESS>");
        return;
      }
      await addWallet(userId, address);
      await ctx.reply("Wallet added.");
      return;
    }
    if (sub === "remove") {
      const address = args[1];
      if (!address) {
        await ctx.reply("Usage: /wallets remove <TRON_ADDRESS>");
        return;
      }
      await removeWallet(userId, address);
      await ctx.reply("Wallet removed (if existed).");
      return;
    }
    if (sub === "fav" || sub === "favorite") {
      const address = args[1];
      if (!address) {
        await ctx.reply("Usage: /wallets favorite <TRON_ADDRESS>");
        return;
      }
      await setFavoriteWallet(userId, address);
      await ctx.reply("Favorite wallet set.");
      return;
    }
    const wallets = await listWallets(userId);
    if (wallets.length === 0) {
      await ctx.reply("No wallets saved. Use /wallets add <address> to add one.");
    } else {
      const lines = wallets.map(w => `${w.address}${w.is_favorite ? " (favorite)" : ""}`);
      await ctx.reply(lines.join("\n"));
    }
  });
}
