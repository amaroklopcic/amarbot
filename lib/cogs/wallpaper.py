import os
import random
from datetime import timezone
from typing import List, Literal, Optional

import aiocron
import aiohttp
import cloudscraper
from bs4 import BeautifulSoup
from discord import ChannelType, Interaction, app_commands
from discord.ext import commands

from lib.logging import get_logger


class DailyWallpapersCog(commands.GroupCog, group_name="walls"):
    """Wallpaper related commands and daily random wallpapers."""

    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()

        self.logger = get_logger(__name__)
        self.logger.debug("Initializing DailyWallpapersCog...")

        self.bot = bot
        self.cron_job = aiocron.crontab(
            "0 12 * * *", func=self.post_daily_wall, loop=self.bot.loop, tz=timezone.utc
        )

    async def make_request(self, url: str, method: str = "GET", **kwargs):
        session = aiohttp.ClientSession()

        try:
            resp = await session.request(
                method=method,
                url=url,
                **kwargs,
            )
            await session.close()
            resp.raise_for_status()
            return resp
        except (
            aiohttp.ClientError,
            aiohttp.http_exceptions.HttpProcessingError,
        ) as e:
            status = getattr(e, "status", None)
            message = getattr(e, "message", None)
            self.logger.exception(
                f"aiohttp exception occurred - {url} [{status}]: {message}"
            )
            raise
        except Exception as e:
            self.logger.exception("Non-aiohttp exception occurred")
            raise

    async def fetch_wallpapers(
        self,
        category: List[Literal["general", "anime", "people"]],
        purity: List[Literal["sfw", "sketchy"]],
        query: Optional[str] = None,
        ai_art: bool | None = None,
    ):
        base_url = "https://wallhaven.cc/search"

        categories_param = (
            f"{'general' in category and 1 or 0}"
            f"{'anime' in category and 1 or 0}"
            f"{'people' in category and 1 or 0}"
        )
        purity_param = f"{'sfw' in purity and 1 or 0}{'sketchy' in purity and 1 or 0}0"

        params = {
            "categories": categories_param,
            "purity": purity_param,
            "atleast": "2560x1440",
            "ratios": "landscape",
            "sorting": "random",
            "order": "desc",
        }

        if ai_art is not None:
            params["ai_art_filter"] = f"{ai_art is True and 1 or 0}"

        if query is not None:
            params["q"] = query

        try:
            scraper = cloudscraper.create_scraper()
            resp = scraper.get(url=base_url, params=params)

            text = resp.text

            soup = BeautifulSoup(text)
            thumbs_section = soup.find("section", class_="thumb-listing-page")
            thumbnails = thumbs_section.ul.find_all("li")
            self.logger.debug(f"found {len(thumbnails)} image thumbnails")

            image_urls = []
            for thumbnail in thumbnails:
                figure = thumbnail.find("figure")
                image_id = figure.get("data-wallpaper-id")
                image_group = image_id[:2]
                info = figure.find("div", class_="thumb-info")

                # get image extention
                image_ext = None
                if info.find("span", class_="png"):
                    # check to make sure image is not a png
                    image_ext = "png"
                else:
                    data_src = thumbnail.find("figure").find("img").get("data-src")
                    image_ext = data_src.split(".")[-1]

                endpoint = f"/full/{image_group}/wallhaven-{image_id}.{image_ext}"
                full_image_url = "https://w.wallhaven.cc" + endpoint

                image_urls.append(full_image_url)

            scraper.close()

            return image_urls

        except Exception as e:
            self.logger.exception("Exception when parsing wallpapers")
            raise

    async def post_daily_wall(self):
        """Posts a daily high-quality wallpaper to the `#wallpapers` channel."""
        self.logger.debug("Posting daily wallpaper...")

        channel_name = "wallpapers"
        image_urls = await self.fetch_wallpapers(category=["general"], purity=["sfw"])

        for guild in self.bot.guilds:
            for channel in guild.channels:
                if channel.type == ChannelType.text and channel.name == channel_name:
                    await channel.send(random.choice(image_urls))

    @app_commands.command()
    @app_commands.describe(
        filters="Possible filters: general, anime, people, ai, sketchy"
    )
    async def random(self, interaction: Interaction, filters: Optional[str] = None):
        """Sends a random high-quality wallpaper."""
        self.logger.debug("Getting a random wallpaper...")

        await interaction.response.defer()

        filters = filters or ""

        category = []
        if "general" in filters:
            category.append("general")
        if "anime" in filters:
            category.append("anime")
        if "people" in filters:
            category.append("people")

        image_urls = await self.fetch_wallpapers(
            category=category,
            purity=["sketchy" if "sketchy" in filters else "sfw"],
            ai_art=[True if "ai" in filters else None],
        )

        await interaction.followup.send(random.choice(image_urls))

    @app_commands.command()
    @app_commands.describe(
        query="Search query (e.g. \"City\" or \"Dog\")",
        filters="Possible filters: general, anime, people, ai, sketchy"
    )
    async def search(
        self, interaction: Interaction, query: str, filters: Optional[str] = None
    ):
        """Search for a high-quality wallpaper."""
        self.logger.debug("Searching for a wallpaper...")

        await interaction.response.defer()

        filters = filters or ""

        category = []
        if "general" in filters:
            category.append("general")
        if "anime" in filters:
            category.append("anime")
        if "people" in filters:
            category.append("people")

        image_urls = await self.fetch_wallpapers(
            query=query,
            category=category,
            purity=["sketchy" if "sketchy" in filters else "sfw"],
            ai_art=[True if "ai" in filters else None],
        )

        await interaction.followup.send(random.choice(image_urls))
