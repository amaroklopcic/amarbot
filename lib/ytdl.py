import youtube_dl, discord, asyncio
from functools import partial

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
	'format': 'bestaudio/best',
	'outtmpl': 'downloads/%(id)s-%(title)s.%(ext)s',
	'restrictfilenames': True,
	# 'noplaylist': True,
	'reconnect': True,
	'reconnect_streamed': True,
	'reconnect_delay_max': '5',
	# 'skip_download': True,
	# 'debug_printtraffic': True,
	'nocheckcertificate': True,
	'ignoreerrors': False,
	'logtostderr': False,
	'quiet': True,
	'no_warnings': True,
	'default_search': 'auto',
	'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
	'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):

	def __init__(self, source, *, data, volume=1.0):
		super().__init__(source, volume)
		self.data = data
		self.title = data.get('title')
		self.url = data.get('url')


	@classmethod
	async def fetch_info(self, query, *, loop=None):
		loop = loop or asyncio.get_event_loop()
		data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
		if 'entries' in data:
			return data['entries'][0]
		else:
			return None

	# TODO: removing @classmethod causes TypeError: fetch_info requires 1 postional arg "query"
	# see why this happens
	@classmethod
	async def regather_stream(cls, data, *, loop):
		"""Used for preparing a stream, instead of downloading.
		Since Youtube Streaming links expire."""
		loop = loop or asyncio.get_event_loop()
		# requester = data['requester']

		to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
		data = await loop.run_in_executor(None, to_run)
		print("returning from regather stream...")
		
		return cls(discord.FFmpegPCMAudio(data['url']), data=data)

	@classmethod
	async def from_url(cls, url, *, loop=None, stream=False):

		loop = loop or asyncio.get_event_loop()

		data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

		if 'entries' in data:
			data = data['entries'][0]

		filename = data['url'] if stream else ytdl.prepare_filename(data)
		return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
		
	@classmethod
	def from_file(cls, filename):
		return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data={"duration": 1})