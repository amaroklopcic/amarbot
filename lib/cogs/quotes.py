import os
from datetime import timezone

import aiocron
import aiohttp
from discord import ChannelType
from discord.ext import commands

from lib.logging import get_logger


class Quotes(commands.Cog):
    """Commands related to quotes from famous people. Uses the "They Said So" API.

    Currently only features a cronjob that runs at 7am every day (CST), which fetches
    the quote of the day and posts it to the "quote-of-the-day" text channel if it
    exists.

    https://theysaidso.com/
    """

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()

        self.logger = get_logger(__name__)
        self.logger.debug("Initializing QuotesCog...")

        self.bot = bot
        self.base_url = "https://quotes.rest"
        self.api_token = os.environ.get("THEYSAIDSO_API_TOKEN")
        self.qod_cron = aiocron.crontab(
            "0 12 * * *", func=self.qod, loop=self.bot.loop, tz=timezone.utc
        )

    async def make_request(self, url: str, method: str = "GET", **kwargs):
        if not self.api_token:
            raise Exception("No API token in environment")

        session = aiohttp.ClientSession()

        full_url = f"{self.base_url}{url}"

        try:
            resp = await session.request(
                method=method,
                url=full_url,
                headers={"X-TheySaidSo-Api-Secret": self.api_token},
                **kwargs,
            )
            await session.close()
            resp.raise_for_status()
            return await resp.json()
        except (
            aiohttp.ClientError,
            aiohttp.http_exceptions.HttpProcessingError,
        ) as e:
            status = getattr(e, "status", None)
            message = getattr(e, "message", None)
            self.logger.exception(
                f"aiohttp exception occurred - {full_url} [{status}]: {message}"
            )
            raise
        except Exception as e:
            self.logger.exception("Non-aiohttp exception occurred")
            raise

    async def qod(self):
        """Check for a quote of the day channel and post a quote of the day in there
        if one exists.
        """
        self.logger.debug("Posting quote of the day...")

        # category = "all"
        category = "inspire"
        channel_name = "quote-of-the-day"

        try:
            resp = await self.make_request(f"/qod.json?category={category}")
            self.logger.debug(resp)
            author = resp["contents"]["quotes"][0]["author"]
            quote = resp["contents"]["quotes"][0]["quote"]
        except Exception as e:
            self.logger.exception("Failed to parse response for quote of the day")
            raise

        for guild in self.bot.guilds:
            for channel in guild.channels:
                if channel.type == ChannelType.text and channel.name == channel_name:
                    await channel.send(f'*"{quote}"* - {author}')
