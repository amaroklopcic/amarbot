import discord
from discord import app_commands
from discord.ext import commands


class UtilsCog(commands.GroupCog, group_name="utils"):
    @app_commands.command()
    async def count(self, interaction: discord.Interaction):
        """Returns total number of text messages from author in a channel."""
        await interaction.response.defer()
        count = 0
        channel = interaction.channel
        author = interaction.user
        async for message in channel.history(limit=None):
            if message.author == author:
                count += 1
        await interaction.followup.send(
            f"{author.mention} has {count} total text messages in this channel."
        )

    @app_commands.command()
    async def channel_count(self, interaction: discord.Interaction):
        """Returns total number of text messages in a channel."""
        await interaction.response.defer()
        count = 0
        channel = interaction.channel
        async for message in channel.history(limit=None):
            count += 1
        await interaction.followup.send(
            f"There are a total of {count} text messages in the channel."
        )
