from discord.ext import commands

from lib.cogs.cog import CommonCog
from lib.ytdl import YTDLSource


# TODO: add pause/resume, skips, queue system, and maybe audio scrubbing
class MusicCog(CommonCog):
    """Commands related to playing music."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self._queue = []
        self.last_ctx: commands.Context | None = None
        self.current_song_task = None

    def start_next_song(self):
        self._queue.pop(0)
        if len(self._queue) > 0:
            self.current_song_task = self.bot.loop.create_task(
                self._play(self.last_ctx, self._queue[0])
            )

    @commands.command()
    async def play(self, ctx: commands.Context, *, url):
        """Plays from a url (almost anything youtube_dl supports)"""

    async def _play(self, ctx: commands.Context, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            self._queue[0] = f"{player.title}"
            ctx.voice_client.play(player, after=lambda e: self.on_song_finish(e))
            self.last_ctx = ctx

        await ctx.send(f"Now playing: {player.title}")

    def on_song_finish(self, error):
        if error:
            print(f"Player error: {error}")

        # self.start_next_song()

    @commands.command()
    async def play(self, ctx: commands.Context, *, url):
        """Plays from a query or url (almost anything youtube_dl supports)"""
        try:
            self._queue.pop(0)
        except IndexError:
            self._queue.append(url)

        await self._play(ctx, url)

    @commands.command()
    async def volume(self, ctx: commands.Context, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        # TODO: add some input validation here
        ctx.voice_client.source.volume = volume / 100

        await ctx.send(f"Changed volume to {volume}%")

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
    async def queue(self, ctx: commands.Context, *, url: str | None = None):
        """Add a song to the queue. If no url is provided, shows the current queue."""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        if url:
            async with ctx.typing():
                # instead of holding the player in memory until it gets played, just add
                # the title so we can regrab it later, since youtube invalidates the links
                # after some time
                self._queue.append(url)
                await ctx.send(f"Added to queue: {url} ({len(self._queue)} in queue)")
        else:
            async with ctx.typing():
                if len(self._queue) == 0:
                    await ctx.send("No songs in the queue")
                    return

                list_str = "Songs in the current queue:\n"
                for index, song_name in enumerate(self._queue):
                    list_str += f"> {index + 1}. {song_name}"
                    if index == 0:
                        list_str += " *(currently playing)*\n"
                    else:
                        list_str += "\n"

                await ctx.send(list_str.strip())

    @commands.command()
    async def pop(self, ctx: commands.Context, *, index: int):
        """Remove a song from the queue at index (default last)"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        async with ctx.typing():
            if len(self._queue) < 2:
                await ctx.send("No songs in the queue")
                return

            song_name = self._queue.pop(index and index - 1 or -1)
            await ctx.send(
                f"Removed from queue: {song_name} ({len(self._queue)} in queue)"
            )

    @commands.command()
    async def list(self, ctx: commands.Context):
        """List out the current queue"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        async with ctx.typing():
            if len(self._queue) == 0:
                await ctx.send("No songs in the queue")
                return

            list_str = "Songs in the current queue:\n"
            for index, song_name in enumerate(self._queue):
                list_str += f"> {index + 1}. {song_name}"
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

        ctx.voice_client.stop()
        self._queue.pop(0)

        if len(self._queue) > 0:
            async with ctx.typing():
                player = await YTDLSource.from_url(
                    self._queue[0], loop=self.bot.loop, stream=True
                )
                ctx.voice_client.play(player, after=lambda e: self.on_song_finish(e))
                self.last_ctx = ctx

            await ctx.send(f"Now playing: {player.title}")

    @commands.command()
    async def stop(self, ctx: commands.Context):
        """Stops and disconnects the bot from voice"""
        await self.disconnect_vc(ctx)

    @play.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        await self.join_authors_vc(ctx)
