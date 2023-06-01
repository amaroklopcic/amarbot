from discord.ext import commands

from lib.cogs.cog import CommonCog
from lib.ytdl import YTDLSource


# TODO: add pause/resume, skips, queue system, and maybe audio scrubbing
class MusicCog(CommonCog):
    """Commands related to playing music."""

    @commands.command()
    async def play(self, ctx: commands.Context, *, url):
        """Plays from a url (almost anything youtube_dl supports)"""
        await self.acknowledge(ctx)

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(
                player, after=lambda e: print(f"Player error: {e}") if e else None
            )

        await ctx.send(f"Now playing: {player.title}")
        await self.finish(ctx)

    @commands.command()
    async def volume(self, ctx: commands.Context, volume: int):
        """Changes the player's volume"""
        await self.acknowledge(ctx)

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        # TODO: add some input validation here
        ctx.voice_client.source.volume = volume / 100

        await ctx.send(f"Changed volume to {volume}%")
        await self.finish(ctx)

    @commands.command()
    async def stop(self, ctx: commands.Context):
        """Stops and disconnects the bot from voice"""
        await self.disconnect_vc(ctx)

    @play.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        await self.join_authors_vc(ctx)
