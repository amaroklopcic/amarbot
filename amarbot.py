import discord, asyncio, os, random, datetime
from discord.ext import commands
from ytdl import YTDLSource

client = commands.Bot(command_prefix = '.')

class AmarBot:

	def __init__(self, filesize_restriction=None):
		self.voice_client = None

	@staticmethod
	async def acknowledge(context):
		await context.message.add_reaction("⏳")

	@staticmethod
	async def finish(context, delete_after=None):
		await context.message.remove_reaction("⏳", client.user)
		await context.message.add_reaction("☑")
		if isinstance(delete_after, (int, float)):
			await context.message.edit(delete_after=delete_after)

	async def channel_count(self, context):
		"""Returns total number of text messages in a channel"""
		await self.acknowledge(context)
		messages = len(await context.message.channel.history(limit=None).flatten())
		await context.message.channel.send(
			f"There are a total of {messages} *text* messages in the channel."
		)
		await self.finish(context)

	async def count(self, context):
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

	@staticmethod
	def filter_message(content="", filters=None):
		if content != "" and not isinstance(filters, (list, set, tuple)):
			raise Exception(
				f"""filter_message called with content, filters = {type(content)} {type(filters)}
				and expected str and list/set/tuple of str."""
			)

		str_strip = lambda string: string.replace("*", "").replace("!", "")

		should_pass = 0
		shouldnt_pass = 0

		for clean in filters:
			if "*" in clean and not "\*" in clean:
				if "!" in clean and not "\!" in clean:
					if str_strip(clean).lower() in content.lower():
						shouldnt_pass += 1
				else:
					if str_strip(clean).lower() in content.lower():
						should_pass += 1
			else:
				if "!" in clean and not "\!" in clean:
					if str_strip(clean).lower() in content.lower().split(" "):
						shouldnt_pass += 1
				else:
					if str_strip(clean).lower() in content.lower().split(" "):
						should_pass += 1

		if shouldnt_pass > 0:
			return False
		elif should_pass > 0:
			return True

		return False

	async def history(self, context, args):
		await self.acknowledge(context)
		counter = 0
		concatented_str = ""
		at_user = f"{context.message.author.mention}:\n"
		async for message in context.message.channel.history(limit=None):
			if message.id != context.message.id and message.author == context.message.author and not message.pinned:
				if self.filter_message(message.content, args):
					counter += 1
					# doing this because of Discords 2000 char limit in messages
					if len(at_user + concatented_str + message.content) + 6 > 2000:
						await context.message.channel.send(at_user + concatented_str, delete_after=60.0)
						concatented_str = ""
					else:
						concatented_str += "> - " + message.content + "\n"

		if len(concatented_str) > 0:
			await context.message.channel.send(at_user, delete_after=60.0)
			await context.message.channel.send(concatented_str, delete_after=60.0)

		await context.message.channel.send(f"Found {counter} instances from {context.message.author.mention}...", delete_after=60.0)
		await self.finish(context, delete_after=60.0)

	async def clear(self, args, context):
		"""
			Searches through entire history of a text channel and 
			removes any messages that match the given keywords
		"""
		await self.acknowledge(context)
		counter = 0
		concatented_str = ""
		at_user = f"{context.message.author.mention}:\n"
		for message in await context.message.channel.history(limit=None).flatten():
			if message.id != context.message.id and message.author == context.message.author and not message.pinned:
				if self.filter_message(message.content, args):
					counter += 1
					# doing this because of Discords 2000 char limit in messages
					if len(at_user + concatented_str + message.content) + 6 > 2000:
						await context.message.channel.send(at_user + concatented_str, delete_after=60.0)
						concatented_str = ""
					else:
						concatented_str += "> - " + message.content + "\n"
					await message.delete()
						
		if len(concatented_str) > 0:
			await context.message.channel.send(at_user + concatented_str, delete_after=60.0)
			concatented_str = ""

		await context.message.channel.send(f"Removing {counter} instances from {context.message.author.mention}...", delete_after=60.0)
		await self.finish(context, delete_after=60.0)

	async def clear_bot_messages(self, context):
		"""
			Searches through entire text channel history of the bot and 
			removes all messages that are not pinned.
		"""
		await self.acknowledge(context)
		counter = 0
		at_user = f"{context.message.author.mention}:\n"
		for message in await context.message.channel.history(limit=None).flatten():
			if message.id != context.message.id and message.author == client.user and not message.pinned:
				counter += 1
				await message.delete()

		await context.message.channel.send(f"Removing {counter} instances from {client.user.mention}...", delete_after=60.0)
		await self.finish(context, delete_after=60.0)

	async def stop(self, context=None):
		if self.voice_client is not None:
			self.voice_client.stop()
		await context.message.add_reaction("🛑")

	async def quote(self, context):
		await self.acknowledge(context)
		random_date = datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 365*2))
		for mention in context.message.mentions:
			messages = await context.message.channel.history(limit=1000, before=random_date).flatten()
			mention_quotes = list(filter(lambda user: user.author == mention, messages))
			if len(mention_quotes) > 0:
				rando_msg = random.choice(mention_quotes)
				await context.message.channel.send(
					f"""\"{rando_msg.content}\" 
					- {mention.nick or mention.display_name} {rando_msg.created_at.year}/{rando_msg.created_at.month}/{rando_msg.created_at.day}"""
				)
			else:
				await context.message.channel.send(
					f"no quotes found before {random_date.year}/{random_date.month}/{random_date.day} 😭"
				)
			await self.finish(context)

	async def join(self, context):

		if context.message.author.voice is None:
			await context.message.channel.send(
				"You must be in a voice channel to use this command!"
			)
			return False
		else:
			voice_channel = context.message.author.voice.channel
			try:
				self.voice_client = await voice_channel.connect()
			except discord.ClientException:
				await self.voice_client.move_to(voice_channel)

		return True

	async def leave(self):
		self.voice_client = await self.voice_client.edit(voice_channel=None)

	# meme commands ⬇⬇⬇
	async def russian_roulette(self, context=None):
		"""Randomly selects a user and disconnects them from the channel."""
		for role in context.message.author.roles:
			if role.permissions.manage_permissions is not True:
				await context.message.add_reaction("🚫")
				return

		if context is not None:
			success = await self.join(context)
			if not success:
				return
		else:
			return

		voice_channel = context.message.author.voice.channel

		if len(voice_channel.members) > 0:
			chosen_one = random.choice(voice_channel.members)
			player = YTDLSource.from_file("sounds/roulette.wav")

			# connect to voice channel and play sound
			await self.join(context)
			self.voice_client.play(player)

			# sleep so user can hear gunshot
			await asyncio.sleep(player.data["duration"])
			await chosen_one.edit(voice_channel=None)

			await self.stop()
			await self.leave()

	async def driveby(self, context=None):
		"""Plays machine gun sound while kicking people from the voice channel."""
		for role in context.message.author.roles:
			if role.permissions.manage_permissions is not True:
				await context.message.add_reaction("🚫")
				return

		if context is not None:
			success = await self.join(context)
			if not success:
				return
		else:
			return

		voice_channel = context.message.author.voice.channel

		if len(voice_channel.members) > 0:

			player = await YTDLSource.from_url("K0op6i9ydnM", stream=False)

			await self.join(context)
			self.voice_client.play(player)

			# initial wait so everyone can here the "CHK CHK"
			await asyncio.sleep(1)

			edited_members = voice_channel.members

			for user in edited_members:
				if user.bot:
					edited_members.remove(user)

			# keep going until they all dead cuz
			while edited_members:
				await asyncio.sleep(random.uniform(1, 2))
				user = random.choice(edited_members)
				if user.bot and len(edited_members) == 1:
					break
				elif user.bot:
					continue
				await user.edit(voice_channel=None)
				edited_members.remove(user)

			await self.stop()
			await self.leave()

	async def grenade(self, context=None):
		"""Plays grenade sound while everyone is scattered."""
		for role in context.message.author.roles:
			if role.permissions.manage_permissions is not True:
				await context.message.add_reaction("🚫")
				return

		if context is not None:
			success = await self.join(context)
			if not success:
				return
		else:
			return

		voice_channel = context.message.author.voice.channel

		if len(voice_channel.members) > 0:

			player = await YTDLSource.from_url("grenade sound effect", stream=True)

			await self.join(context)
			self.voice_client.play(player)

			all_voice_channels = voice_channel.guild.voice_channels

			# sleep so user can hear gunshot
			await asyncio.sleep(player.data["duration"])

			# To avoid kicking them into a channel they dont have access to
			for member in voice_channel.members:
				if member.bot:
					continue
				available_channels = []
				for channel in all_voice_channels:
					if channel.permissions_for(member).connect:
						available_channels.append(channel)
				await member.edit(voice_channel=random.choice(available_channels))

			await self.stop()
			await self.leave()



bot = AmarBot()

@client.event
async def on_ready():
	print(f"Logged in as {client.user.name} (ID: {client.user.id})")
	print("--------------------")

@client.command(pass_context=True)
async def max_count(context):
	await bot.max_count(context)

@client.command(pass_context=True)
async def count(context):
	await bot.count(context)

@client.command(pass_context=True)
async def clear(context, *args):
	await bot.clear(args, context)

@client.command(pass_context=True)
async def clear_bot_messages(context):
	await bot.clear_bot_messages(context)

@client.command(pass_context=True)
async def history(context, *args):
	await bot.history(context, args)

@client.command(pass_context=True)
async def vote(context):
	await bot.vote(context)

@client.command(pass_context=True)
async def quote(context):
	await bot.quote(context)

# stop command just to stop other commands in there tracks
@client.command(pass_context=True)
async def stop(context):
	await bot.stop(context)

# meme commands ⬇⬇⬇
@client.command(pass_context=True)
async def roulette(context):
	await bot.russian_roulette(context)

@client.command(pass_context=True)
async def driveby(context):
	await bot.driveby(context)

@client.command(pass_context=True)
async def grenade(context):
	await bot.grenade(context)

client.run("NjExNDY3NjE2NTY5MjYyMDgx.Xec5RQ.jyoKEesLLLWUFKqW6bcXl1Cvghs")