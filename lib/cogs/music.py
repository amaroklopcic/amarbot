import asyncio
from typing import List, Optional, Mapping

from discord import Interaction, app_commands, File
from discord.ext.commands.bot import Bot
from discord.ext.commands.cog import GroupCog

from lib.logging import get_logger
from lib.ytdl import YTDLSource, YTDLSourcesController
from lib.common import join_users_vc


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

    def delete_controller(self, interaction: Interaction):
        guild_id = interaction.guild.id
        if guild_id in self.controllers.keys():
            del self.controllers[guild_id]

    async def check_voice(self, interaction: Interaction):
        ctx = await self.bot.get_context(interaction)
        if ctx.voice_client is None:
            return await interaction.response.send_message(
                "Not connected to a voice channel."
            )
        return ctx.voice_client

    @app_commands.command()
    @app_commands.describe(
        query='A generic query (e.g. "adele set fire to the rain") or a URL'
    )
    async def play(self, interaction: Interaction, *, query: str):
        """Plays from a query or url (almost anything youtube_dl supports)"""
        await interaction.response.defer()

        # TODO: before we fetch the query, we should parse the URL and see if it's a
        # playlist, and update the chat with something like: this is a playlist, this
        # will take a while
        # TODO: adding a song that already exists in the controller should not be
        # redownloaded
        # TODO: this command should replace the current playing song, currently it just
        # adds it to the queue
        controller = self.get_controller(interaction)
        await controller.insert(query)
        source = controller.current_source
        await controller.wait_for_ready_state()

        voice_client = await join_users_vc(self.bot, interaction)
        voice_client.play(controller)

        await interaction.followup.send(f"Now playing {source.metadata['title']}!")

    @app_commands.command()
    async def stop(self, interaction: Interaction):
        """Stops the player and disconnects the bot from voice."""
        self.logger.debug(f"Stopping the music player in {interaction.guild.name}...")
        await interaction.response.defer()

        ctx = await self.bot.get_context(interaction)
        if ctx.voice_client:
            await ctx.voice_client.disconnect()

        controller = self.get_controller(interaction)
        controller.cleanup()
        self.delete_controller(interaction)

        await interaction.followup.send("Goodbye!")

    @app_commands.command()
    async def grab(self, interaction: Interaction):
        """Sends a downloadable mp3 of the current playing song to the channel."""
        await interaction.response.defer()

        # TODO: validate this isn't a livestream and the song isn't too large to send
        # to a Discord channel (we should be able to check max file size limit for the
        # specific guild)

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
        # TODO: needs to be tested
        voice_client = await self.check_voice(interaction)
        if not voice_client:
            return

        if volume < 1 or volume > 100:
            return await interaction.response.send_message(
                "Volume must be a number in the range of 1-100."
            )

        controller = self.get_controller(interaction)
        controller.volume = volume / 100

        await interaction.response.send_message(f"Changed volume to {volume}%")

    @app_commands.command()
    async def pause(self, interaction: Interaction):
        """Pause the music player."""
        # TODO: needs to be tested
        voice_client = await self.check_voice(interaction)
        if not voice_client:
            return

        voice_client.pause()

    @app_commands.command()
    async def resume(self, interaction: Interaction):
        """Resume the music player."""
        # TODO: needs to be tested
        voice_client = await self.check_voice(interaction)
        if not voice_client:
            return

        voice_client.resume()

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
        # TODO: throws if there is no controller or bot is not in channel
        controller = self.get_controller(interaction)
        controller.next()
        title = controller.current_source.metadata["title"]
        await interaction.response.send_message(f"Now playing *{title}*!")

    @app_commands.command()
    async def back(self, interaction: Interaction):
        """Play the previous song in the queue."""
        # TODO: throws if there is no controller or bot is not in channel
        controller = self.get_controller(interaction)
        controller.back()
        title = controller.current_source.metadata["title"]
        await interaction.response.send_message(f"Now playing *{title}*!")

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
