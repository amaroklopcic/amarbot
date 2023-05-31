import asyncio
import datetime
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

from lib.ytdl import YTDLSource

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix = '.', intents=intents)

class AmarBot:
	def __init__(self, filesize_restriction=None):
		self.voice_client = None

	@staticmethod
	async def acknowledge(context: commands.Context):
		await context.message.add_reaction("⏳")

	@staticmethod
	async def finish(context: commands.Context, delete_after=None):
		await context.message.remove_reaction("⏳", client.user)
		await context.message.add_reaction("☑")
		if isinstance(delete_after, (int, float)):
			await context.message.edit(delete_after=delete_after)

	async def count(self, context: commands.Context):
		"""Returns total number of text messages from author in a channel."""
		await self.acknowledge(context)
		counter = 0
		author = context.message.author.mention
		async for message in context.message.channel.history(limit=None):
			if message.author == context.message.author:
				counter += 1
		await context.message.channel.send(
			f"{author} has {counter} total *text* messages in this channel."
		)
		await self.finish(context)


if __name__ == "__main__":
	bot = AmarBot()

	@client.event
	async def on_ready():
		print(f"Logged in as {client.user.name} (ID: {client.user.id})")
		print("--------------------")

	@client.command(pass_context=True)
	async def count(context):
		await bot.count(context)

	client.run(os.environ.get("AMARBOT_TOKEN"))
