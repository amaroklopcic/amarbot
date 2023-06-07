from discord.ext import commands

from lib.cogs.cog import CommonCog
from lib.ytdl import YTDLSource


# TODO: add pause/resume, skips, queue system, and maybe audio scrubbing
class MusicCog(CommonCog):
    """Commands related to playing music."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self._queue = []

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
    async def pause(self, ctx: commands.Context):
        """Pause the music player"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.pause()

    @commands.command()
    async def resume(self, ctx: commands.Context):
        """Resume the music player"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.resume()

    @commands.command()
    async def queue(self, ctx: commands.Context, *, url: str):
        """Add a song to the queue"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            await ctx.send(
                f"Added to queue: {player.title} ({len(self._queue)} in queue)"
            )
            self._queue.append(player)

    @commands.command()
    async def pop(self, ctx: commands.Context, *, index: str):
        """Remove a song from the queue at index (default last)"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        async with ctx.typing():
            if len(self._queue) < 2:
                await ctx.send("No songs in the queue")
                return

            player = self._queue.pop(index or -1)
            await ctx.send(
                f"Removed from queue: {player.title} ({len(self._queue)} in queue)"
            )

    @commands.command()
    async def list(self, ctx: commands.Context):
        """List out the current queue"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        async with ctx.typing():
            list_str = "Songs in the current queue:\n"
            for index, player in enumerate(self._queue):
                list_str += f"> {index + 1}. {player.title}"
                if index == 0:
                    list_str += " *(currently playing)*\n"
                else:
                    list_str += "\n"

            await ctx.send(list_str.strip())            

    @commands.command()
    async def skip(self, ctx: commands.Context):
        """Skip the current playing song"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        async with ctx.typing():
            pass

    @commands.command()
    async def stop(self, ctx: commands.Context):
        """Stops and disconnects the bot from voice"""
        await self.disconnect_vc(ctx)

    @play.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        await self.join_authors_vc(ctx)
