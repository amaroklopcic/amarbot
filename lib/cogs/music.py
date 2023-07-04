import asyncio
from typing import List, Optional, Mapping

from discord import Interaction, app_commands, File
from discord.ext.commands.bot import Bot
from discord.ext.commands.cog import GroupCog

from lib.logging import get_logger
from lib.ytdl import YTDLSource, YTDLSourcesController
from lib.common import join_users_vc


# TODO: refactor the entire cog to support multiple music controllers for different
# channels
# TODO: adjust the controoler to steam the first song to avoid delays, and download the
# song in the background at the same time. songs added to a queue should be set to download
# TODO: add a /progress command that returns something like this: ...............|........ 2:15 / 3:22
# TODO: add a /repeat command that repeats songs in a queue or a specific song

class MusicCog(GroupCog, group_name="yt"):
    """Commands related to playing music."""

    def __init__(self, bot: Bot) -> None:
        super().__init__()

        self.logger = get_logger(__name__)
        self.logger.debug("Initializing MusicCog...")

        self.bot = bot
        self.controllers: Mapping[str, YTDLSourcesController] = {}

    def get_controller(self, interaction: Interaction):
        """Fetch the music controller for the interactions guild, creating it if it
        doesn't exist.
        """
        guild_id = interaction.guild.id
        controller = self.controllers.get(guild_id)
        if controller is not None:
            return controller
        else:
            self.controllers[guild_id] = YTDLSourcesController(loop=self.bot.loop)
            return self.controllers[guild_id]

    @app_commands.command()
    @app_commands.describe(
        query='A generic query (e.g. "adele set fire to the rain") or a URL'
    )
    async def play(self, interaction: Interaction, *, query: str):
        """Plays from a query or url (almost anything youtube_dl supports)"""
        await interaction.response.defer()

        controller = self.get_controller(interaction)
        player = await controller.insert(query)
        await controller.wait_for_ready_state()

        voice_client = await join_users_vc(self.bot, interaction)
        voice_client.play(controller)

        await interaction.followup.send(f"Now playing {player.metadata['title']}!")

    @app_commands.command()
    async def grab(self, interaction: Interaction):
        """Sends a downloadable mp3 of the current playing song to the channel."""
        await interaction.response.defer()

        controller = self.get_controller(interaction)
        source = controller.current_source

        if source is None:
            await interaction.followup.send("There is no song currently playing")
            return

        # await interaction.followup.send("waiting for song to finish downloading...")
        await source.wait_for_download_ready_state()
        # await interaction.followup.edit_message("converting song to mp3...")
        filename = await source.write_buffer_to_file()

        await interaction.followup.send(file=File(filename))

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
        await interaction.response.defer()
        # source = await YTDLSource.from_url(query, loop=self.bot.loop, stream=False)
        # player = YTPlayer(query, loop=self.bot.loop)
        # await player.wait_for_ready_state()
        # print("player ready!")
        # print(await player.download())
        # print("download finished")
        await interaction.followup.send(f"Here's yo file dawg:")

    @app_commands.command()
    @app_commands.describe(
        query='A generic query (e.g. "adele set fire to the rain") or a URL'
    )
    async def mp4(self, interaction: Interaction, query: str):
        """Send an mp4 download link to the channel."""
