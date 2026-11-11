"""
ZYRO Music System
Development by ARIAN

Commands:
+play / +p <song name or url>
+join / +j
+leave / +dc / +stop
+skip / +s
+pause / +resume
+queue / +q
+nowplaying / +np
+volume / +vol
+musichelp
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
from emojis import MUSIC, CHECK, CROSS, VOICE, INFO, LOADING, FIRE, STAR

# yt-dlp options
YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "extract_flat": False,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}


class MusicPlayer:
    def __init__(self, ctx: commands.Context):
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        self.current = None
        self.volume = 0.5
        self.voice = ctx.voice_client
        self.ctx = ctx
        self.task = self.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        await self.bot.wait_until_ready()
        while True:
            self.next.clear()
            try:
                source = await asyncio.wait_for(self.queue.get(), timeout=180)
            except asyncio.TimeoutError:
                if self.voice and self.voice.is_connected():
                    await self.channel.send(f"{INFO} Queue empty for 3 minutes. Leaving...")
                    await self.voice.disconnect()
                return

            self.current = source
            try:
                self.voice.play(
                    discord.FFmpegPCMAudio(source["url"], **FFMPEG_OPTIONS),
                    after=lambda e: self.bot.loop.call_soon_threadsafe(self.next.set)
                )
                self.voice.source = discord.PCMVolumeTransformer(self.voice.source, volume=self.volume)
                
                embed = discord.Embed(
                    title=f"{MUSIC} Now Playing",
                    description=f"**[{source['title']}]({source['webpage_url']})**\n"
                                f"Duration: `{source.get('duration_string', 'Live')}`\n"
                                f"Requested by: {source['requester'].mention}",
                    color=0x5865F2
                )
                if source.get("thumbnail"):
                    embed.set_thumbnail(url=source["thumbnail"])
                embed.set_footer(text="ZYRO Music • Development by ARIAN")
                await self.channel.send(embed=embed)
            except Exception as e:
                await self.channel.send(f"{CROSS} Playback error: `{e}`")
                self.next.set()
                continue

            await self.next.wait()
            self.current = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players = {}

    def get_player(self, ctx: commands.Context) -> MusicPlayer:
        player = self.players.get(ctx.guild.id)
        if not player:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player
        return player

    async def cog_unload(self):
        for player in self.players.values():
            player.task.cancel()

    async def ensure_voice(self, ctx: commands.Context):
        if not ctx.author.voice:
            await ctx.send(f"{CROSS} You must be in a voice channel.")
            return False
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
        elif ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
        return True

    async def search_yt(self, query: str):
        """Try multiple search strategies so song is found more reliably"""
        loop = asyncio.get_event_loop()
        strategies = []

        # If it's already a URL
        if "youtube.com" in query or "youtu.be" in query or query.startswith("http"):
            strategies = [query]
        else:
            strategies = [
                f"ytsearch1:{query}",
                f"ytsearch5:{query}",
                query,
            ]

        last_error = None
        for attempt in strategies:
            try:
                opts = YDL_OPTIONS.copy()
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = await loop.run_in_executor(None, lambda: ydl.extract_info(attempt, download=False))
                
                if not info:
                    continue
                if "entries" in info:
                    entries = [e for e in info["entries"] if e]
                    if not entries:
                        continue
                    info = entries[0]

                return {
                    "url": info["url"],
                    "title": info.get("title", "Unknown"),
                    "webpage_url": info.get("webpage_url", query),
                    "thumbnail": info.get("thumbnail"),
                    "duration_string": info.get("duration_string") or (f"{info['duration']//60}:{info['duration']%60:02d}" if info.get("duration") else "Live"),
                }, None
            except Exception as e:
                last_error = str(e)
                continue

        return None, last_error or "No results found"

    # ==================== COMMANDS ====================

    @commands.command(name="join", aliases=["j", "connect"])
    async def join(self, ctx: commands.Context):
        if not await self.ensure_voice(ctx):
            return
        await ctx.send(f"{CHECK} {VOICE} Joined **{ctx.author.voice.channel.name}**")

    @commands.command(name="leave", aliases=["dc", "disconnect", "stop"])
    async def leave(self, ctx: commands.Context):
        if not ctx.voice_client:
            return await ctx.send(f"{CROSS} Not connected.")
        player = self.players.pop(ctx.guild.id, None)
        if player:
            player.task.cancel()
        await ctx.voice_client.disconnect()
        await ctx.send(f"{CHECK} Disconnected & queue cleared.")

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str = None):
        if not query:
            return await ctx.send(f"{CROSS} Usage: `{ctx.prefix}play <song name or url>`")

        if not await self.ensure_voice(ctx):
            return

        msg = await ctx.send(f"{LOADING} Searching...")

        data, error = await self.search_yt(query)
        if error or not data:
            return await msg.edit(content=f"{CROSS} Could not find anything.\n`{error}`")

        data["requester"] = ctx.author
        player = self.get_player(ctx)

        await player.queue.put(data)

        if player.current:
            await msg.edit(content=f"{CHECK} Added to queue: **{data['title']}**")
        else:
            await msg.edit(content=f"{CHECK} Playing: **{data['title']}**")

    @commands.command(name="skip", aliases=["s", "next"])
    async def skip(self, ctx: commands.Context):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send(f"{CROSS} Nothing is playing.")
        ctx.voice_client.stop()
        await ctx.send(f"{CHECK} Skipped.")

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(f"{CHECK} Paused.")
        else:
            await ctx.send(f"{CROSS} Nothing is playing.")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send(f"{CHECK} Resumed.")
        else:
            await ctx.send(f"{CROSS} Not paused.")

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx: commands.Context):
        player = self.players.get(ctx.guild.id)
        if not player or (player.queue.empty() and not player.current):
            return await ctx.send(f"{INFO} Queue is empty.")

        embed = discord.Embed(title=f"{MUSIC} Queue", color=0x5865F2)
        if player.current:
            embed.add_field(name="Now Playing", value=f"**{player.current['title']}**", inline=False)

        upcoming = list(player.queue._queue)[:10]
        if upcoming:
            text = "\n".join(f"`{i+1}.` {s['title']}" for i, s in enumerate(upcoming))
            embed.add_field(name="Up Next", value=text, inline=False)
        else:
            embed.add_field(name="Up Next", value="Nothing", inline=False)

        embed.set_footer(text="ZYRO Music • Development by ARIAN")
        await ctx.send(embed=embed)

    @commands.command(name="nowplaying", aliases=["np"])
    async def nowplaying(self, ctx: commands.Context):
        player = self.players.get(ctx.guild.id)
        if not player or not player.current:
            return await ctx.send(f"{CROSS} Nothing is playing.")
        s = player.current
        embed = discord.Embed(
            title=f"{MUSIC} Now Playing",
            description=f"**[{s['title']}]({s['webpage_url']})**\nRequested by {s['requester'].mention}",
            color=0x5865F2
        )
        if s.get("thumbnail"):
            embed.set_thumbnail(url=s["thumbnail"])
        await ctx.send(embed=embed)

    @commands.command(name="volume", aliases=["vol"])
    async def volume(self, ctx: commands.Context, vol: int = None):
        player = self.players.get(ctx.guild.id)
        if not player:
            return await ctx.send(f"{CROSS} Nothing is playing.")
        if vol is None:
            return await ctx.send(f"{INFO} Current volume: `{int(player.volume*100)}%`")
        if not 0 <= vol <= 100:
            return await ctx.send(f"{CROSS} Volume must be 0-100")
        player.volume = vol / 100
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = player.volume
        await ctx.send(f"{CHECK} Volume set to `{vol}%`")

    @commands.command(name="musichelp", aliases=["mhelp"])
    async def musichelp(self, ctx: commands.Context):
        embed = discord.Embed(
            title=f"{MUSIC} ZYRO Music Commands",
            description=(
                f"`{ctx.prefix}play <name/url>` / `{ctx.prefix}p` — Play a song\n"
                f"`{ctx.prefix}join` / `{ctx.prefix}j` — Join VC\n"
                f"`{ctx.prefix}leave` / `{ctx.prefix}dc` — Leave + clear queue\n"
                f"`{ctx.prefix}skip` / `{ctx.prefix}s` — Skip current\n"
                f"`{ctx.prefix}pause` / `{ctx.prefix}resume`\n"
                f"`{ctx.prefix}queue` / `{ctx.prefix}q` — Show queue\n"
                f"`{ctx.prefix}nowplaying` / `{ctx.prefix}np`\n"
                f"`{ctx.prefix}volume <0-100>`\n\n"
                f"**Development by ARIAN**"
            ),
            color=0x5865F2
        )
        await ctx.send(embed=embed)

    # ==================== SLASH ====================
    @app_commands.command(name="play", description="Play a song")
    @app_commands.describe(query="Song name or YouTube URL")
    async def slash_play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        ctx = await commands.Context.from_interaction(interaction)
        if not await self.ensure_voice(ctx):
            return await interaction.followup.send(f"{CROSS} Join a voice channel first.")
        
        data, error = await self.search_yt(query)
        if error or not data:
            return await interaction.followup.send(f"{CROSS} Not found.")

        data["requester"] = interaction.user
        player = self.get_player(ctx)
        await player.queue.put(data)

        if player.current:
            await interaction.followup.send(f"{CHECK} Added: **{data['title']}**")
        else:
            await interaction.followup.send(f"{CHECK} Playing: **{data['title']}**")

    @app_commands.command(name="skip", description="Skip current song")
    async def slash_skip(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await interaction.response.send_message(f"{CHECK} Skipped.")
        else:
            await interaction.response.send_message(f"{CROSS} Nothing playing.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
