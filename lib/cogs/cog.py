import asyncio

import discord
from discord.ext import commands


class CommonCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    async def sleep(self, duration: float):
        await asyncio.sleep(duration)

    async def acknowledge(self, context: commands.Context):
        """Adds a timer emoji to users issued command."""
        await context.message.add_reaction("⏳")

    async def finish(self, context: commands.Context):
        """Removes timer emoji and adds checkmark emoji to users issued command."""
        await context.message.remove_reaction("⏳", self.bot.user)
        await context.message.add_reaction("☑")

    async def join_channel(
        self, ctx: commands.Context, *, channel: discord.VoiceChannel
    ):
        """Joins a voice channel."""
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def join(self, ctx: commands.Context, *, channel: discord.VoiceChannel):
        """Joins a voice channel."""
        self.join_channel(ctx, channel=channel)

    @commands.command()
    async def stop(self, ctx: commands.Context):
        """Disconnects the bot from voice channel."""
        await ctx.voice_client.disconnect()
