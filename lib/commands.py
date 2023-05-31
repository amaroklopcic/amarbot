from discord.ext import commands


async def command_count(context: commands.Context):
    """Returns total number of text messages from author in a channel."""
    count = 0
    author = context.message.author.mention
    async for message in context.message.channel.history(limit=None):
        if message.author == context.message.author:
            count += 1
    await context.message.channel.send(
        f"{author} has {count} total text messages in this channel."
    )


async def command_channel_count(context: commands.Context):
    count = 0
    async for message in context.message.channel.history(limit=None):
        count += 1
    await context.message.channel.send(
        f"There are a total of {count} text messages in the channel."
    )
