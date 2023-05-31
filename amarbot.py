import asyncio
import datetime
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

from lib.ytdl import YTDLSource
from lib.commands import command_count

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("--------------------")

async def acknowledge(context: commands.Context):
    await context.message.add_reaction("⏳")

async def finish(context: commands.Context):
    await context.message.remove_reaction("⏳", bot.user)
    await context.message.add_reaction("☑")

@bot.command()
async def count(context: commands.Context):
    """Returns total number of text messages from author in a channel."""
    await acknowledge(context)
    await command_count(context)
    await finish(context)


if __name__ == "__main__":
    load_dotenv()
    bot.run(os.environ.get("AMARBOT_TOKEN"))
