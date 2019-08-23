import discord, asyncio, os, random
from discord.ext import commands
from ytdl import YTDLSource

client = commands.Bot(command_prefix = '.')

class AmarBot():

	def __init__(self, filesize_restriction=None):
		self.queue = []
		self.voice_client = None
		self.player = None
		self.last_context = None # any time function runs with context passed, update this to that context
		self.song_finished = False # asynchronously checking this var to detect when to play next song 
		self.filesize_restriction = filesize_restriction # 1e+7 = 10mb, 1e+8 = 100mb
		self.loop = asyncio.get_event_loop()
		self.bg_task = self.loop.create_task(self.check_queue())

	# Music Commands
	async def play(self, args, context=None):

		if not context is None:
			success = await self.join(context)
			if not success:
				return

		query = " ".join(args)

		if self.voice_client.is_playing() or self.voice_client.is_paused():
			await self.add_to_queue(query, context)
			return

		# Calling this already downloads file.
		# The bit below it returning if filesize is too large is redundant
		# Will add this functionality later probably
		self.player = await YTDLSource.from_url(query, stream=False)

		if not self.filesize_restriction is None and self.player.data["filesize"] < self.filesize_restriction:
			await context.message.channel.send(f'"{self.player.data["title"]}" file size is too large!')
			return

		if not context is None:
			await context.message.channel.send(
				f'Now playing "{self.player.data["title"]}"\n{self.player.data["webpage_url"]}'
			)
		elif not self.last_context is None:
			await self.last_context.message.channel.send(
				f'Now playing "{self.player.data["title"]}"\n{self.player.data["webpage_url"]}'
			)

		self.song_finished = False
		self.voice_client.play(self.player, after=lambda e: print('Player Error: %s' % e) if e else self.song_after(self.player.data["id"]))

	def song_after(self, song_id):
		self.song_finished = True
		for file_name in os.listdir():
			if song_id in file_name:
				os.remove(file_name)

	async def queue_next(self): 
		if self.queue:
			song = self.queue.pop(0)
			await self.stop()
			await self.play((song))

	async def add_to_queue(self, query, context=None):
		self.queue.append(query)
		if not context is None:
			self.last_context = context
			await context.message.channel.send(f'"{query}" has been added to queue!')

	async def stop(self, context=None):
		if not self.voice_client is None:
			self.voice_client.stop()
		if not context is None:
			self.last_context = context
			await context.message.channel.send("Music stopped!")

	async def pause(self, context=None):
		if not self.voice_client is None:
			self.voice_client.pause()
		if not context is None:
			self.last_context = context
			await context.message.channel.send("Music paused!")

	async def resume(self, context=None):
		if not self.voice_client is None:
			self.voice_client.resume()
		if not context is None:
			self.last_context = context
			await context.message.channel.send("Music resumed!")

	async def skip(self, context):
		await self.stop()
		await context.message.channel.send(f'"{self.player.data["title"]}" was skipped!')
		await self.queue_next()

	async def join(self, context):

		self.last_context = context

		if context.message.author.voice is None:
			await context.message.channel.send(
				"You must be in a voice channel to use this command!"
			)
			return False
		else:
			voice_channel = context.message.author.voice.channel
			try:
				self.voice_client = await voice_channel.connect()
			except discord.ClientException: # if bot is in another voice channel
				await self.voice_client.move_to(voice_channel)

		return True

	async def leave(self):
		self.voice_client = await self.voice_client.edit(voice_channel=None)

	async def check_queue(self):
		while True:
			if self.song_finished:
				await self.queue_next()
			await asyncio.sleep(1) # task runs every 1 second

	# Fun Commands (must pass context, else will return)
	async def russian_roulette(self, context=None):
		# Randomly selects a user to be kicked from the voice channel
		if not context is None:
			success = await self.join(context)
			if not success:
				return
		else:
			return

		voice_channel = context.message.author.voice.channel
		# message_channel = context.message.channel

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
		# Bot plays machine gun sound while everyone gets kicked from voice channel
		if not context is None:
			success = await self.join(context)
			if not success:
				return
		else:
			return

		voice_channel = context.message.author.voice.channel
		# message_channel = context.message.channel

		if len(voice_channel.members) > 0:

			# prepare gunshot sound
			player = await YTDLSource.from_url("K0op6i9ydnM", stream=True)

			# connect to voice channel and start playing sound
			await self.join(context)
			self.voice_client.play(player)

			# initial wait so everyone can here the "CHK CHK"
			await asyncio.sleep(1)

			edited_members = voice_channel.members

			# remove all other bots from this list and exlude them from the driveby
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
		# Bot plays grenade sound while everyone gets 
		# scattered across all available voice channels in the curent server
		if not context is None:
			success = await self.join(context)
			if not success:
				return
		else:
			return

		voice_channel = context.message.author.voice.channel
		# message_channel = context.message.channel

		if len(voice_channel.members) > 0:

			# prepare gunshot sound
			player = await YTDLSource.from_url("grenade sound effect", stream=True)

			# connect to voice channel and start playing sound
			await self.join(context)
			self.voice_client.play(player)

			all_voice_channels = voice_channel.guild.voice_channels

			# sleep so user can hear gunshot
			await asyncio.sleep(player.data["duration"])

			for member in voice_channel.members:
				if member.bot:
					continue
				available_channels = [] # channels available to the member in the current iteration
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
async def play(context, *args):
	await bot.play(args, context=context)

@client.command(pass_context=True)
async def stop(context):
	await bot.stop(context)

@client.command(pass_context=True)
async def pause(context):
	await bot.pause(context)

@client.command(pass_context=True)
async def resume(context):
	await bot.resume(context)

@client.command(pass_context=True)
async def skip(context):
	await bot.skip(context)

@client.command(pass_context=True)
async def roulette(context):
	await bot.russian_roulette(context)

@client.command(pass_context=True)
async def driveby(context):
	await bot.driveby(context)

@client.command(pass_context=True)
async def grenade(context):
	await bot.grenade(context)



client.run(os.environ.get("AmarBot_Token"))