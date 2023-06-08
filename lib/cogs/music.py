import asyncio
from typing import List

from discord.ext import commands

from lib.cogs.cog import CommonCog
from lib.ytdl import YTDLSource


class MusicCog(CommonCog):
    """Commands related to playing music."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.controller = MusicController(bot.loop)

    @commands.command()
    async def play(self, ctx: commands.Context, *, url):
        """Plays from a query or url (almost anything youtube_dl supports)"""
        async with ctx.typing():
            self.controller.update_ctx(ctx)
            # TODO: this resets the queue, intended behavior is supposed to be
            # replacing index 0 with the new song so the queue can continue
            # playing once the song finishes
            try:
                self.controller.queue[0] = url
            except IndexError:
                self.controller.push(url)
            self.controller.play()
            await self.controller.on_player_start()

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

        self.controller.pause()

    @commands.command()
    async def resume(self, ctx: commands.Context):
        """Resume the music player"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        self.controller.resume()

    @commands.command()
    async def queue(self, ctx: commands.Context, *, url: str | None = None):
        """Add a song to the queue. If no url is provided, shows the current queue."""
        if url:
            async with ctx.typing():
                self.controller.push(url)
                await ctx.send(
                    f"Added to queue: {url} ({len(self.controller.queue)} in queue)"
                )
        else:
            async with ctx.typing():
                if len(self.controller.queue) == 0:
                    await ctx.send("No songs in the queue")
                    return

                list_str = "Songs in the current queue:\n"
                for index, song_name in enumerate(self.controller.queue):
                    list_str += f"> {index + 1}. {song_name}"
                    if index == 0:
                        list_str += " *(currently playing)*\n"
                    else:
                        list_str += "\n"

                await ctx.send(list_str.strip())

    @commands.command()
    async def pop(self, ctx: commands.Context, *, index: int):
        """Remove a song from the queue at index (default last)"""
        async with ctx.typing():
            if len(self.controller.queue) < 2:
                await ctx.send("No songs in the queue to remove")
                return

            song_name = self.controller.pop(index and index - 1 or None)
            await ctx.send(
                f"Removed from queue: {song_name} ({len(self.controller.queue)} in queue)"
            )

    @commands.command()
    async def skip(self, ctx: commands.Context):
        """Skip the current playing song"""
        self.controller.skip()

    @commands.command()
    async def stop(self, ctx: commands.Context):
        """Stops and disconnects the bot from voice"""
        await self.disconnect_vc(ctx)

    @play.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        await self.join_authors_vc(ctx)


class MusicController:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.queue: List[str] = []
        self.ctx: commands.Context | None = None
        self.player: YTDLSource | None = None
        self.is_stopped = False

        self._song_task: asyncio.Task | None = None
        self._song_started_event: asyncio.Event = asyncio.Event()
        self._song_finished_event: asyncio.Event = asyncio.Event()

        # kick off event loop
        self._update_task = self.loop.create_task(self.update_loop())

    def update_ctx(self, ctx: commands.Context):
        self.ctx = ctx

    async def update_loop(self):
        # run update loop every 1 second
        await asyncio.sleep(1)

        # schedule next song to be played
        if not self.is_stopped and not self._song_task:
            if len(self.queue) > 0:
                self._song_task = self.loop.create_task(self._play())

        # schedule next update
        self._update_task = self.loop.create_task(self.update_loop())

    async def _play(self):
        print("_play")
        next_song = self.queue[0]

        self.player = await YTDLSource.from_url(next_song, loop=self.loop, stream=True)
        self.queue[0] = f"{self.player.title}"
        self.ctx.voice_client.play(self.player, after=lambda e: self._on_song_finish(e))

        self._song_started_event.set()
        await self.ctx.send(f"Now playing: {self.player.title}")

        await self._song_finished_event.wait()

    def _on_song_finish(self, error):
        # TODO: check and make sure this is still getting ran after we run the stop
        # command
        print("_on_song_finish")
        if error:
            print(f"Player error: {error}")

        self.queue.pop(0)
        self.loop.call_soon_threadsafe(self._song_finished_event.set)
        self.loop.call_soon_threadsafe(self._song_started_event.clear)
        self._song_task = None

    def play(self):
        """Plays a song from the top of the queue.

        Returns a `asyncio.Task` that doesnt resolve until the song is
        done playing.
        """
        self.is_stopped = False

    def stop(self):
        """Stops the current song and removes it from the queue. Does not schedule
        the next song.
        """
        self.ctx.voice_client.stop()
        self._song_task.cancel()
        self.queue.pop(0)
        self.is_stopped = True
        self._song_task = None

    def pause(self):
        """Pauses the current playing song."""
        self.ctx.voice_client.pause()

    def resume(self):
        """Resumes the current playing song."""
        self.ctx.voice_client.resume()

    def push(self, url: str):
        """Insert a url into the queue"""
        # instead of holding the player in memory until it gets played, just add
        # the title so we can regrab it later, since youtube invalidates the links
        # after some time
        self.queue.append(url)

    def pop(self, index: int):
        """Remove a song from the queue and return the name."""
        return self.queue.pop(index)

    def skip(self):
        """Skip the currently playing song and schedule the next one in the queue."""
        self.ctx.voice_client.stop()
        # self.queue.pop(0)

    # -vvv- events -vvv-
    async def on_player_start(self):
        """Blocking call that resolves when the players starts playing a song.

        Resolves instantly if a song is currently playing.
        """
        await self._song_started_event.wait()

    async def on_player_finish(self):
        """Blocking call that resolves when the players finishes playing a song.

        Resolves instantly if a song has already finished playing.
        """
        await self._song_finished_event.wait()

    def __delattr__(self, __name: str) -> None:
        # TODO: remove next update task from event loop
        pass
