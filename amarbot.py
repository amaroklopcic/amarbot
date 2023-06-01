import asyncio
import datetime
import os
import random

import discord
from discord.ext import commands
from discord.utils import MISSING, setup_logging
from dotenv import load_dotenv

from lib.cogs.commands import CommandsCog
from lib.cogs.memes import MemeCog
from lib.cogs.music import MusicCog

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("--------------------")


async def main():
    async with bot:
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
