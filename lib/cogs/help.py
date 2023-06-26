from typing import List

from discord import Interaction, app_commands
from discord.app_commands.commands import Command, Group
from discord.ext import commands

from lib.logging import get_logger


class HelpCog(commands.Cog):
    """Provides a help command to show all the commands available."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot
        self.logger = get_logger(__name__)
        self.logger.debug("Initializing HelpCog...")

    @app_commands.command()
    async def help(self, interaction: Interaction):
        """Sends a private message showing available commands and usage."""

        groups: List[Group] = []
        for command in self.bot.tree.walk_commands():
            if isinstance(command, Group):
                groups.append(command)

        for group in groups:
            help_msg = f"\n\n**/{group.name}**\n*{group.description}*"
            group_name = f"{group.name} "
            for command in group.commands:
                if isinstance(command, Group):
                    # this command is a subgroup, we don't utilize this functionality,
                    # so we'll just throw for now
                    raise NotImplementedError("Command subgroup detected")
                elif isinstance(command, Command):
                    help_msg += f"\n- /{group_name}{command.name}\n"
                    help_msg += command.description

            await interaction.user.send(help_msg)

        await interaction.response.send_message("DM Sent!", ephemeral=True)
