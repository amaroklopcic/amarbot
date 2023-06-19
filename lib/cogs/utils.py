import os
import json

import discord
from discord import ChannelType, app_commands
from discord.ext import commands


def is_admin(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator


def is_owner(interaction: discord.Interaction):
    return interaction.user.id == interaction.guild.owner_id


class UtilsCog(commands.GroupCog, group_name="utils"):
    @app_commands.command()
    @app_commands.check(is_admin)
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
    @app_commands.check(is_admin)
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

    @app_commands.command()
    @app_commands.check(is_owner)
    async def export_guild(self, interaction: discord.Interaction):
        """Returns all the messages from all the channels in a Discord guild."""
        await interaction.response.defer()

        text_channels = []
        for channel in interaction.guild.channels:
            if channel.type == ChannelType.text:
                text_channels.append(channel)

        exported_messages = []
        for channel in text_channels:
            async for message in channel.history(limit=None):
                channel_name = channel.name
                author = message.author
                content = message.content
                attachments = message.attachments
                created_at = message.created_at
                exported_messages.append(
                    {
                        "channel_name": channel_name,
                        "author_name": author.name,
                        "content": content,
                        "created_at": created_at.isoformat(),
                    }
                )

        # make sure path exists
        exports_dir = f"{os.getcwd()}/exports"
        if not os.path.exists(exports_dir):
            os.makedirs(exports_dir)

        filename = f"exports/{interaction.guild.name}-export.json"
        file = open(
            file=filename,
            mode="w",
            encoding="utf_8",
            errors="strict",
        )
        json.dump(exported_messages, file, indent=4)
        file.close()

        success_text = (
            f"Successfully extracted {len(exported_messages)} messages "
            f"from {len(text_channels)} channels. Check your DMs!"
        )

        await interaction.followup.send(success_text)
        await interaction.user.send(file=discord.File(filename))
