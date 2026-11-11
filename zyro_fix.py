"""
ZYRO Fix - Simple Reliable Version
Development by ARIAN
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import re
import aiosqlite
from pathlib import Path

# Safe import
try:
    from emojis import CHECK, CROSS, INFO, MUSIC, STAR, FIRE, ZYRO
except Exception:
    CHECK = "✅"
    CROSS = "❌"
    INFO = "ℹ️"
    MUSIC = "🎵"
    STAR = "✦"
    FIRE = "🔥"
    ZYRO = "⚡"

DB = Path("db/zyro_extra.db")

def parse_time(t: str):
    t = t.lower().strip()
    m = re.match(r"^(\d+)(s|m|h|d)$", t)
    if not m:
        return None
    val, unit = int(m.group(1)), m.group(2)
    return val * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]


class ZyroFix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("[ZYRO FIX] Cog __init__ called")

    async def cog_load(self):
        print("[ZYRO FIX] cog_load started")
        Path("db").mkdir(exist_ok=True)
        async with aiosqlite.connect(DB) as db:
            await db.execute("CREATE TABLE IF NOT EXISTS noprefix (user_id INTEGER PRIMARY KEY, expires REAL)")
            await db.execute("CREATE TABLE IF NOT EXISTS dmaccess (user_id INTEGER PRIMARY KEY, expires REAL)")
            await db.commit()

        # Remove premium lock
        removed = 0
        for check in list(self.bot._checks):
            if getattr(check, "__name__", "") == "premium_global_lock":
                self.bot.remove_check(check)
                removed += 1
        print(f"[ZYRO FIX] Premium checks removed: {removed}")

        # Force remove old help
        for name in ("help", "h", "commands"):
            try:
                self.bot.remove_command(name)
            except Exception:
                pass
        print("[ZYRO FIX] Old help removed")

        self.bot.loop.create_task(self._delayed_sync())
        print("[ZYRO FIX] Loaded successfully ✓")

    async def _delayed_sync(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(3)
        try:
            synced = await self.bot.tree.sync()
            print(f"[ZYRO FIX] Slash commands synced: {len(synced)}")
        except Exception as e:
            print(f"[ZYRO FIX] Sync failed: {e}")

    # ========== TEST COMMAND (to confirm cog is loaded) ==========
    @commands.command(name="zyro")
    async def zyro_test(self, ctx):
        await ctx.send(f"{CHECK} **ZYRO Fix is LOADED and working!**\nDevelopment by ARIAN")

    # ========== CLEAN HELP ==========
    @commands.command(name="help", aliases=["h"])
    async def help_cmd(self, ctx, category: str = None):
        p = ctx.prefix
        if category:
            maps = {
                "mod": f"`{p}ban` `{p}kick` `{p}mute` `{p}purge` `{p}lock`",
                "music": f"`{p}play <song>` `{p}skip` `{p}queue` `{p}join` `{p}leave`",
                "antinuke": f"`{p}antinuke enable` `{p}whitelist` `{p}wl`",
                "owner": f"`{p}np add @user 10m` `{p}dmaccess @user 10m` `{p}dm @user msg`",
            }
            text = maps.get(category.lower(), "Unknown category")
            return await ctx.send(embed=discord.Embed(title=category.title(), description=text, color=0x5865F2))

        embed = discord.Embed(
            title=f"{ZYRO} ZYRO Help",
            description=(
                f"**Prefix:** `{p}`\n"
                f"**Development by ARIAN**\n\n"
                f"`{p}help mod`\n"
                f"`{p}help music`\n"
                f"`{p}help antinuke`\n"
                f"`{p}help owner`\n\n"
                f"Test: `{p}zyro`"
            ),
            color=0x5865F2
        )
        await ctx.send(embed=embed)

    # ========== NO PREFIX ==========
    @commands.command(name="np")
    @commands.is_owner()
    async def np(self, ctx, action: str = None, user: discord.Member = None, duration: str = None):
        if action == "add" and user and duration:
            sec = parse_time(duration)
            if not sec:
                return await ctx.send(f"{CROSS} Use time like `10m` `1h` `2d`")
            async with aiosqlite.connect(DB) as db:
                await db.execute("INSERT OR REPLACE INTO noprefix VALUES (?, ?)", (user.id, time.time() + sec))
                await db.commit()
            return await ctx.send(f"{CHECK} No-Prefix given to {user.mention} for **{duration}**")
        if action == "remove" and user:
            async with aiosqlite.connect(DB) as db:
                await db.execute("DELETE FROM noprefix WHERE user_id=?", (user.id,))
                await db.commit()
            return await ctx.send(f"{CHECK} Removed from {user.mention}")
        await ctx.send(f"{INFO} `{ctx.prefix}np add @user 10m`\n`{ctx.prefix}np remove @user`")

    # ========== DM ACCESS ==========
    @commands.command(name="dmaccess")
    @commands.is_owner()
    async def dmaccess(self, ctx, user: discord.Member, duration: str):
        sec = parse_time(duration)
        if not sec:
            return await ctx.send(f"{CROSS} Use `10m` / `1h` etc")
        async with aiosqlite.connect(DB) as db:
            await db.execute("INSERT OR REPLACE INTO dmaccess VALUES (?, ?)", (user.id, time.time() + sec))
            await db.commit()
        await ctx.send(f"{CHECK} DM Access given to {user.mention} for **{duration}**")

    @commands.command(name="dm")
    async def dm(self, ctx, user: discord.Member, *, msg: str):
        allowed = False
        if await self.bot.is_owner(ctx.author):
            allowed = True
        else:
            async with aiosqlite.connect(DB) as db:
                async with db.execute("SELECT expires FROM dmaccess WHERE user_id=?", (ctx.author.id,)) as cur:
                    row = await cur.fetchone()
            if row and row[0] > time.time():
                allowed = True
        if not allowed:
            return await ctx.send(f"{CROSS} No DM Access. Owner can give with `+dmaccess @you 10m`")
        try:
            await user.send(f"**From {ctx.author} via ZYRO:**\n{msg}")
            await ctx.send(f"{CHECK} Sent to {user.mention}")
        except Exception:
            await ctx.send(f"{CROSS} Could not DM that user.")

    # ========== FIXSTATUS ==========
    @commands.command(name="fixstatus")
    async def fixstatus(self, ctx):
        await ctx.send(
            f"{CHECK} **ZYRO Fix is Active**\n"
            f"Commands available:\n"
            f"`+zyro`  ← test command\n"
            f"`+help`  ← clean help\n"
            f"`+np add @user 10m`\n"
            f"`+dmaccess @user 10m`\n"
            f"`+dm @user message`\n"
            f"**Development by ARIAN**"
        )


async def setup(bot):
    await bot.add_cog(ZyroFix(bot))
    print("[ZYRO FIX] setup() completed")
