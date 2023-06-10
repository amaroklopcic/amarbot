import asyncio
import datetime
import os
import random

import discord
from discord.ext import commands
from discord.utils import MISSING, setup_logging
from dotenv import load_dotenv

from lib.cogs.ack import Acknowledge
from lib.cogs.commands import CommandsCog
from lib.cogs.memes import MemeCog
from lib.cogs.music import MusicCog

COMMAND_PREFIX = "."

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=COMMAND_PREFIX,
    intents=intents,
    activity=discord.Activity(
        type=discord.ActivityType.listening, name=f"{COMMAND_PREFIX}help"
    ),
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("--------------------")


async def main():
    async with bot:
        await bot.add_cog(Acknowledge(bot))
        await bot.add_cog(CommandsCog(bot))
        await bot.add_cog(MusicCog(bot))
        await bot.add_cog(MemeCog(bot))
        await bot.start(os.environ.get("AMARBOT_TOKEN"))


if __name__ == "__main__":
    load_dotenv()

    setup_logging(
        handler=MISSING,
        formatter=MISSING,
        level=MISSING,
        root=False,
    )

    asyncio.run(main(), debug=True)
