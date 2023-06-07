import asyncio

import discord
from discord.ext import commands


class CommonCog(commands.Cog):
    emoji_ack = "⏳"
    emoji_finish = "☑️"
    emoji_reject = "🚫"
    emoji_error = "⚠️"

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    # -vvv- helper methods -vvv-
    async def sleep(self, duration: float):
        await asyncio.sleep(duration)

    # -vvv- emoji reactions -vvv-
    async def acknowledge(self, ctx: commands.Context):
        """Adds `emoji_ack` to users issued command."""
        await ctx.message.add_reaction(self.emoji_ack)
        # TODO: check if user has sufficient privileges
        # for role in ctx.message.author.roles:
        #     if role.permissions.manage_permissions is not True:
        #         await ctx.message.add_reaction("🚫")
        #         return

    async def finish(self, ctx: commands.Context):
        """Removes `emoji_ack` and adds `emoji_finish` to users issued command."""
        await asyncio.gather(
            ctx.message.add_reaction(self.emoji_finish),
            ctx.message.remove_reaction(self.emoji_ack, self.bot.user),
        )

    async def react_reject(self, ctx: commands.Context):
        """Removes `emoji_ack` and adds `emoji_error` to users issued command."""
        await asyncio.gather(
            ctx.message.add_reaction(self.emoji_reject),
            ctx.message.remove_reaction(self.emoji_ack, self.bot.user),
        )

    async def react_error(self, ctx: commands.Context):
        """Removes `emoji_ack` and adds `emoji_error` to users issued command."""
        await asyncio.gather(
            ctx.message.add_reaction(self.emoji_error),
            ctx.message.remove_reaction(self.emoji_ack, self.bot.user),
        )

    # -vvv- voice channel related commands -vvv-
    async def join_authors_vc(self, ctx: commands.Context):
        """Joins a users voice channel (`ctx.author.voice.channel`)."""
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

    async def join_vc(self, ctx: commands.Context, *, channel: discord.VoiceChannel):
        """Joins a voice channel."""
        return await channel.connect()

    async def disconnect_vc(self, ctx: commands.Context):
        """Disconnects the bot from voice channel."""
        await ctx.voice_client.disconnect()
