import argparse
import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from lib.cogs.ack import AcknowledgeCog
from lib.cogs.help import HelpCog
from lib.cogs.memes import MemeCog
from lib.cogs.music import MusicCog
from lib.cogs.quotes import QuotesCog
from lib.cogs.reminders import RemindersCog
from lib.cogs.sync import SyncCog
from lib.cogs.utils import UtilsCog
from lib.logging import get_logger, setup_discord_logging


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--command_prefix",
        type=str,
        help="command prefix character to use for commands executed on the Discord client",
        default="!",
    )
    parser.add_argument(
        "--no_ack",
        action="store_true",
        help="disable emoji acknowledgments (bot responding to commands with emojis)",
        default=False,
    )
    parser.add_argument(
        "--no_memes",
        action="store_true",
        help="disable all meme-related commands",
        default=False,
    )
    parser.add_argument(
        "--no_music",
        action="store_true",
        help="disable all music-related commands",
        default=False,
    )
    parser.add_argument(
        "--no_qod",
        action="store_true",
        help="disable quote of the day messages",
        default=False,
    )
    parser.add_argument(
        "--no_reminders",
        action="store_true",
        help="disable reminders-related commands",
        default=False,
    )
    parser.add_argument(
        "--no_utils",
        action="store_true",
        help="disable utils-related commands",
        default=False,
    )
    return parser.parse_args()


async def main(
    command_prefix: str,
    no_ack: bool = False,
    no_memes: bool = False,
    no_music: bool = False,
    no_qod: bool = False,
    no_reminders: bool = False,
    no_utils: bool = False,
):
    logger = get_logger("amarbot")
    logger.info("Starting AmarBot...")

    setup_discord_logging()

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
        logger.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")

    async with bot:
        await bot.add_cog(HelpCog(bot))
        await bot.add_cog(SyncCog(bot))

        if not no_ack:
            await bot.add_cog(AcknowledgeCog(bot))
        if not no_memes:
            await bot.add_cog(MemeCog(bot))
        if not no_music:
            await bot.add_cog(MusicCog(bot))
        if not no_qod:
            await bot.add_cog(QuotesCog(bot))
        if not no_reminders:
            await bot.add_cog(RemindersCog(bot))
        if not no_utils:
            await bot.add_cog(UtilsCog(bot))

        await bot.start(os.environ.get("AMARBOT_TOKEN"))


if __name__ == "__main__":
    args = parse_args()

    load_dotenv()

    asyncio.run(
        main(
            command_prefix=args.command_prefix,
            no_ack=args.no_ack,
            no_memes=args.no_memes,
            no_music=args.no_music,
            no_qod=args.no_qod,
            no_reminders=args.no_reminders,
            no_utils=args.no_utils,
        ),
        debug=True,
    )
