import asyncio

import discord
from discord.ext import commands

from lib.logging import get_logger

logger = get_logger(__name__)


async def join_users_vc(
    bot: commands.Bot, interaction: discord.Interaction
) -> discord.VoiceClient | None:
    """Joins a users voice channel (`ctx.author.voice.channel`). Returns the
    `discord.VoiceClient` instantiated from joining the users channel or `None` if
    the user is not in a voice channel.
    """
    ctx = await bot.get_context(interaction)

    if not ctx.valid:
        raise Exception("Retrieved invalid context from interaction")

    try:
        if ctx.author.voice:
            return await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You are not connected to a voice channel.")
    except discord.ClientException:
        # already in a voice channel, move to new channel
        await ctx.voice_client.move_to(ctx.author.voice.channel)
        # NOTE: calling stop just in case something is already playing, but there may
        # be circumstances where we don't want to call this
        ctx.voice_client.stop()
        return ctx.voice_client
    except asyncio.TimeoutError:
        err_msg = "Couldn't connect to the voice client in time"
        await ctx.send(err_msg)
        logger.exception(err_msg)
        raise
    except discord.opus.OpusNotLoaded:
        err_msg = "`libopus` library not found"
        await ctx.send(err_msg)
        logger.exception(err_msg)
        raise
    except Exception:
        err_msg = "Something went wrong when trying to connect to the voice channel"
        await ctx.send(err_msg)
        logger.exception(err_msg)
        raise

    return None
