import discord
from discord.ext import commands

class ZyroPatch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def fixcredit(self, ctx):
        await ctx.send("Development by ARIAN")

    @commands.command()
    @commands.is_owner()
    async def dm(self, ctx, user: discord.User, *, message: str):
        try:
            await user.send(f"**{ctx.author}** থেকে:\n{message}")
            await ctx.reply(f"DM পাঠানো হয়েছে {user.mention} কে।", mention_author=False)
        except Exception as e:
            await ctx.reply(f"DM পাঠানো যায়নি: {e}", mention_author=False)

    @commands.command()
    async def premiumstatus(self, ctx):
        await ctx.reply("Premium system চলছে। Grant করার জন্য: `+premium grant @user 30d`", mention_author=False)

    @commands.command()
    @commands.is_owner()
    async def zyro(self, ctx):
        await ctx.reply("ZYRO patch loaded — Development by ARIAN", mention_author=False)

async def setup(bot):
    await bot.add_cog(ZyroPatch(bot))
