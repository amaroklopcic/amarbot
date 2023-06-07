import discord
from discord.ext import commands

from lib.cogs.cog import CommonCog


class CommandsCog(CommonCog):
    @commands.command()
    async def count(self, ctx: commands.Context):
        """Returns total number of text messages from author in a channel."""
        count = 0
        author = ctx.message.author.mention
        async for message in ctx.message.channel.history(limit=None):
            if message.author == ctx.message.author:
                count += 1
        await ctx.message.channel.send(
            f"{author} has {count} total text messages in this channel."
        )

    @commands.command()
    async def channel_count(self, ctx: commands.Context):
        """Returns total number of text messages in a channel."""
        count = 0
        async for message in ctx.message.channel.history(limit=None):
            count += 1
        await ctx.message.channel.send(
            f"There are a total of {count} text messages in the channel."
        )
