import asyncio
from typing import List, Optional, Mapping

from discord import Interaction, app_commands
from discord.ext.commands.bot import Bot
from discord.ext.commands.cog import GroupCog

from lib.logging import get_logger
from lib.ytdl import YTDLSource


# TODO: refactor the entire cog to support multiple music controllers for different
# channels
# TODO: adjust the controller to download songs instead of streaming them, and
# intelligently delete the downloaded songs, and predownload songs that are in the
# queue
class MusicCog(GroupCog, group_name="yt"):
    """Commands related to playing music."""

    def __init__(self, bot: Bot) -> None:
        super().__init__(bot)

        self.logger = get_logger(__name__)
        self.logger.debug("Initializing MusicCog...")

        self.bot = bot
        self.controllers: Mapping[str, MusicController] = {}

    def get_controller(self, interaction: Interaction):
        # TODO: create the controller if it doesn't exist
        return self.controllers.get(interaction.guild.id)

    @app_commands.command()
    @app_commands.describe(
        query='A generic query (e.g. "adele set fire to the rain") or a URL'
    )
    async def play(self, interaction: Interaction, *, query: str):
        """Plays from a query or url (almost anything youtube_dl supports)"""
        controller = self.get_controller(interaction)

    @app_commands.command()
    @app_commands.describe(volume="Number between 1-100")
    async def volume(self, interaction: Interaction, volume: int):
        """Changes the player's volume."""

    @app_commands.command()
    async def pause(self, interaction: Interaction):
        """Pause the music player."""

    @app_commands.command()
    async def resume(self, interaction: Interaction):
        """Resume the music player."""

    @app_commands.command()
    @app_commands.describe(
        query='A generic query (e.g. "adele set fire to the rain") or a URL'
    )
    async def queue(self, interaction: Interaction, *, query: Optional[str] = None):
        """Add a song to the queue. If no url is provided, shows the current queue."""

    @app_commands.describe(
        index="Number index of the song you want to remove from the queue"
    )
    @app_commands.command()
    async def pop(self, interaction: Interaction, *, index: Optional[int] = None):
        """Remove a song from the queue at index (default last)."""

    @app_commands.command()
    async def next(self, interaction: Interaction):
        """Play the next song in the queue."""

    @app_commands.command()
    async def back(self, interaction: Interaction):
        """Play the previous song in the queue."""

    @app_commands.command()
    async def stop(self, interaction: Interaction):
        """Stops the player and disconnects the bot from voice."""

    @app_commands.command()
    async def scrub(self, interaction: Interaction):
        """Fast-forward or rewind the current playing song."""

    @app_commands.command()
    async def slowed(self, interaction: Interaction):
        """Change the player to play songs 1.5x slower."""

    @app_commands.command()
    async def spedup(self, interaction: Interaction):
        """Change the player to play songs 1.5x faster."""

    @app_commands.command()
    @app_commands.describe(
        query='A generic query (e.g. "adele set fire to the rain") or a URL'
    )
    async def mp3(self, interaction: Interaction, query: str):
        """Send an mp3 download link to the channel."""

    @app_commands.command()
    @app_commands.describe(
        query='A generic query (e.g. "adele set fire to the rain") or a URL'
    )
    async def mp4(self, interaction: Interaction, query: str):
        """Send an mp4 download link to the channel."""


class MusicController:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.logger = get_logger(__name__)
        self.logger.debug("Initializing MusicController...")

        self.queue: List[YTDLSource] = []

    def pause(self):
        """Pauses the current playing song."""
        self.ctx.voice_client.pause()

    def resume(self):
        """Resumes the current playing song."""
        self.ctx.voice_client.resume()

    def insert(self, url: str):
        """Insert a url into the first position of the queue, effectively making it the
        next song to be played.
        """
        try:
            self.queue.insert(0, url)
        except IndexError:
            self.push(url)

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
