import argparse
import asyncio
import os

import discord
from discord.ext import commands
from discord.utils import MISSING, setup_logging
from dotenv import load_dotenv

from lib.cogs.ack import Acknowledge
from lib.cogs.memes import MemeCog
from lib.cogs.music import MusicCog
from lib.cogs.quotes import Quotes
from lib.cogs.reminders import RemindersCog
from lib.cogs.sync import SyncCog
from lib.cogs.utils import UtilsCog


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--command_prefix",
        type=str,
        help="command prefix character to use for commands executed on the Discord client",
        default="!",
    )
    return parser.parse_args()


async def main(command_prefix: str):
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(
        command_prefix=command_prefix,
        intents=intents,
        activity=discord.Activity(
            type=discord.ActivityType.listening, name=f"{command_prefix}help"
        ),
    )

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
        print("--------------------")

    async with bot:
        await bot.add_cog(Acknowledge(bot))
        await bot.add_cog(RemindersCog(bot))
        await bot.add_cog(MusicCog(bot))
        await bot.add_cog(MemeCog(bot))
        await bot.add_cog(Quotes(bot))
        await bot.add_cog(SyncCog(bot))
        await bot.add_cog(UtilsCog(bot))

        await bot.start(os.environ.get("AMARBOT_TOKEN"))


if __name__ == "__main__":
    args = parse_args()

    load_dotenv()

    setup_logging(
        handler=MISSING,
        formatter=MISSING,
        level=MISSING,
        root=False,
    )

    asyncio.run(main(command_prefix=args.command_prefix), debug=True)
