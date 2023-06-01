import discord
from discord.ext import commands

from lib.commands_logic import command_channel_count, command_count


class CommonCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot

    async def acknowledge(self, context: commands.Context):
        await context.message.add_reaction("⏳")

    async def finish(self, context: commands.Context):
        await context.message.remove_reaction("⏳", self.bot.user)
        await context.message.add_reaction("☑")

    async def join_channel(
        self, ctx: commands.Context, *, channel: discord.VoiceChannel
    ):
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def join(self, ctx: commands.Context, *, channel: discord.VoiceChannel):
        """Joins a voice channel."""
        self.join_channel(ctx, channel=channel)

    @commands.command()
    async def stop(self, ctx: commands.Context):
        """Stops and disconnects the bot from voice channel."""
        await ctx.voice_client.disconnect()
