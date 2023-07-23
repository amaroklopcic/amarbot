import asyncio
from typing import List, Optional, Mapping

from discord import Interaction, app_commands, File
from discord.errors import HTTPException
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

    async def get_voice_channel(self, interaction: Interaction):
        """Returns the current `discord.voice_client.VoiceClient` instance."""
        ctx = await self.bot.get_context(interaction)
        return ctx.voice_client

    async def ensure_voice(self, interaction: Interaction):
        """Checks if the bot is connected to a voice channel and returns the
        `discord.voice_client.VoiceClient` instance if it is.
        """
        voice_client = await self.get_voice_channel(interaction)
        if voice_client is None:
            return await interaction.response.send_message(
                "Not connected to a voice channel."
            )
        return voice_client

    @app_commands.command()
    @app_commands.describe(
        query='A generic query (e.g. "adele set fire to the rain") or a URL'
    )
    async def play(self, interaction: Interaction, *, query: str):
        """Plays from a query or url (almost anything youtube_dl supports)."""
        await interaction.response.send_message(
            f"Fetching metadata for query: *{query}*"
        )

        # TODO: adding a song that already exists in the controller should not be
        # redownloaded
        source = await YTDLSource.from_query(query, loop=self.bot.loop)

        controller = self.get_controller(interaction)
        controller.append(source)
        await controller.wait_for_ready_state()

        voice_client = await self.get_voice_channel(interaction)
        if not voice_client:
            voice_client = await join_users_vc(self.bot, interaction)

        if voice_client.is_playing():
            voice_client.source = controller
            if isinstance(source, list):
                await interaction.edit_original_response(
                    content=f"Added a playlist with **{len(source)}** songs to the queue."
                )
            else:
                await interaction.edit_original_response(
                    content=f"Added **{source.full_title}** to the queue."
                )
        else:
            voice_client.play(controller)
            await interaction.edit_original_response(
                content=f"Now playing **{controller.current_source.source.full_title}**!"
            )

    @app_commands.command()
    async def stop(self, interaction: Interaction):
        """Stops the player and disconnects the bot from voice."""
        self.logger.debug(f"Stopping the music player in {interaction.guild.name}...")

        voice_client = await self.ensure_voice(interaction)
        if not voice_client:
            return

        controller = self.get_controller(interaction)
        controller.cleanup()
        self.delete_controller(interaction)

        await voice_client.disconnect()
        voice_client.cleanup()

        await interaction.response.send_message("Goodbye!")

    @app_commands.command()
    async def grab(self, interaction: Interaction):
        """Sends a downloadable mp3 of the current playing song to the channel."""
        controller = self.get_controller(interaction)
        source = controller.current_source

        if source is None:
            await interaction.response.send_message(
                "There is no song currently playing"
            )
            return

        if source.is_livestream:
            await interaction.response.send_message("Can't download a livestream!")
            return

        await interaction.response.defer()
        await interaction.followup.send("Downloading song...")

        await source.wait_for_download_ready_state()

        await interaction.edit_original_response(content="Converting song...")

        filename = await source.write_buffer_to_file()
        file = File(fp=filename, filename=f"{source.metadata['title']}.mp3")

        try:
            await interaction.edit_original_response(
                content="Here's the downloaded song!",
                attachments=[file],
            )
        except HTTPException as e:
            if e.status == 413:
                await interaction.edit_original_response(
                    content=(
                        f"File size exceeds the guild's max file size "
                        f"({(interaction.guild.filesize_limit / 1024) / 1024:.2f} MB)"
                    )
                )
            else:
                err_msg = "Encountered an unexpected issue when trying to send the file"
                await interaction.edit_original_response(content=err_msg)
                self.logger.exception(err_msg)
                raise
        except Exception as e:
            err_msg = "Encountered an unexpected issue when trying to send the file"
            await interaction.edit_original_response(content=err_msg)
            self.logger.exception(err_msg)
            raise

    @app_commands.command()
    @app_commands.describe(volume="Number between 1-100")
    async def volume(self, interaction: Interaction, volume: int):
        """Changes the player's volume."""
        voice_client = await self.ensure_voice(interaction)
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
        voice_client = await self.ensure_voice(interaction)
        if not voice_client:
            return

        voice_client.pause()

        await interaction.response.send_message(f"Paused!")

    @app_commands.command()
    async def resume(self, interaction: Interaction):
        """Resume the music player."""
        voice_client = await self.ensure_voice(interaction)
        if not voice_client:
            return

        voice_client.resume()

        await interaction.response.send_message(f"Resumed!")

    @app_commands.command()
    async def queue(self, interaction: Interaction):
        """Shows the current music queue."""
        voice_client = await self.ensure_voice(interaction)
        if not voice_client:
            return

        controller = self.get_controller(interaction)

        if len(controller.sources) == 0:
            await interaction.response.send_message("No songs in the queue.")
            return
        else:
            list_str = "Songs in the current queue:\n"
            for index, source in enumerate(controller.sources):
                if index == controller.current_source_index:
                    list_str += f"> {index + 1}. **{source.full_title}**\n"
                else:
                    list_str += f"> {index + 1}. {source.full_title}\n"

            await interaction.response.send_message(list_str.strip())

    @app_commands.describe(
        index="Number index of the song you want to remove from the queue"
    )
    @app_commands.command()
    async def pop(self, interaction: Interaction, *, index: Optional[int] = None):
        """Remove a song from the queue at index (default last)."""
        voice_client = await self.ensure_voice(interaction)
        if not voice_client:
            return

        controller = self.get_controller(interaction)

        if len(controller.sources) == 0:
            await interaction.response.send_message("No songs in the queue.")
            return
        elif isinstance(index, int) and index < 1:
            await interaction.response.send_message(f"Index must be higher than 0.")
            return
        elif isinstance(index, int) and index > len(controller.sources):
            await interaction.response.send_message(
                f"No song in the queue at position {index}."
            )
            return

        if isinstance(index, int):
            index = index - 1

        source = controller.pop(index)
        await interaction.response.send_message(
            f"Removed **{source.full_title}** from the queue."
        )

    @app_commands.command()
    async def next(self, interaction: Interaction):
        """Play the next song in the queue."""
        voice_client = await self.ensure_voice(interaction)
        if not voice_client:
            return

        controller = self.get_controller(interaction)

        if controller.current_source_index + 2 > len(controller.sources):
            await interaction.response.send_message("No next song in the queue.")
            return

        controller.next()

        await interaction.response.send_message(
            f"Now playing **{controller.current_source.metadata['title']}**!"
        )

    @app_commands.command()
    async def back(self, interaction: Interaction):
        """Play the previous song in the queue."""
        voice_client = await self.ensure_voice(interaction)
        if not voice_client:
            return

        controller = self.get_controller(interaction)

        if controller.current_source_index - 1 < 0:
            await interaction.response.send_message("No previous song.")
            return

        controller.back()

        await interaction.response.send_message(
            f"Now playing **{controller.current_source.metadata['title']}**!"
        )

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
