import asyncio
import audioop
import math
from io import BufferedIOBase, BytesIO
from time import perf_counter
from typing import Any, List, Mapping

import discord
import youtube_dl
from pydub import AudioSegment

from lib.logging import get_logger

# suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""

YTDL_FORMAT_BESTAUDIO = "bestaudio/best"

# download best mp3 format available (fails if there isnt one available)
YTDL_FORMAT_BESTAUDIO_MP3 = "bestaudio[ext=mp3]"
# download best mp3 format available or any other best if no mp3 is available
YTDL_FORMAT_BESTAUDIO_MP3 = "bestaudio[ext=mp3]/bestaudio/best"
# download best mp4 format available or any other best if no mp4 available
YTDL_FORMAT_BESTAUDIO_MP4 = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

YTDL_FORMAT_OPTIONS = {
    "format": YTDL_FORMAT_BESTAUDIO_MP3,
    "outtmpl": "downloads/audio-%(title)s-%(id)s.%(ext)s",
    "restrictfilenames": True,
    # "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    # bind to ipv4 since ipv6 addresses cause issues sometimes
    "source_address": "0.0.0.0",
}

# ffmpeg -vn option disables video
ffmpeg_options = {"options": "-vn"}

logger = get_logger(__name__)


# TODO: we want to make a spotify sort of fading in/out effect when songs change, to do
# this, we'll need to have one audio stream that has seamless bytes streaming, so the queue,
# would have to be built into some class that handles reading bytes from various audio
# sources, and writes bytes to one audio stream
class YTDLSourcesController(discord.AudioSource):
    """Manages a number of `YTDLSource` objects in a queue and provides a `read` method
    to read from them, cycling them as the sources get exhausted.
    """

    # number of seconds before and after the track to fade in/out the audio
    audio_fade_time = 5.0

    # TODO: add a user defined volume and fade in/out to that volume instead of 1
    def __init__(self, volume: float = 1.0, *, loop: asyncio.AbstractEventLoop) -> None:
        self._volume = volume
        self.loop = loop or asyncio.get_event_loop()

        self.sources: List[YTDLSource] = []
        self.current_source_index = 0

    @property
    def is_ready(self):
        """Checks if the current source is stream-ready."""
        source =  self.current_source
        if source is None or not source.is_stream_ready:
            return False
        return True

    @property
    def current_source(self):
        """Return the current source."""
        try:
            return self.sources[self.current_source_index]
        except IndexError:
            return None

    @property
    def volume(self) -> float:
        """Retrieves or sets the volume as a floating point percentage (e.g. ``1.0`` for
        100%).
        """
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        volume = max(value, 0.0)
        self._volume = volume
        for source in self.sources:
            source.volume = volume

    async def insert(self, query: str):
        """Instantiates a `YTDLSource` from a query and adds it to the queue."""
        new_source = await YTDLSource.from_query(query, loop=self.loop)
        self.sources.append(new_source)
        return new_source

    # def pop(self, index: int):
    #     """Remove a source from the queue."""

    # def next(self):
    #     """Sets the current source index to the next source in the queue."""
    #     self.current_source_index += 1

    # def back(self):
    #     """Sets the current source index to the next source in the queue."""
    #     self.current_source_index -= 1

    async def wait_for_ready_state(self):
        """Coroutine that resolves when the source is ready to start streaming."""
        while self.is_ready is not True:
            await asyncio.sleep(0)
        return True

    def read(self) -> bytes:
        """Reads 20ms worth of audio. Returns silent audio data if the current source
        isn't ready. Returns empty bytes the sources list is empty or if we've reached
        the end of the source and there are no more sources in the queue.
        """
        source = self.current_source

        if source is None:
            return b""        

        if not self.is_ready:
            return AudioSegment.silent(duration=20, frame_rate=48000).raw_data

        # NOTE: need to update get_time_remaining so that it checks the full duration
        # of the song, and not how much audio data is in the buffer
        time_elapsed = source.get_time_elapsed()
        time_remaining = source.get_time_remaining()

        # check to see if source is exhausted
        if time_remaining == 0:
            if len(self.sources) == self.current_source_index + 1:
                logger.debug("all sources exhausted")
                return b""

            if self.sources[self.current_source_index + 1].is_stream_ready:
                logger.debug(
                    f"{source.metadata['title']} has been exhausted, switching to next "
                    "source!"
                )
                self.current_source_index += 1
                return self.read()
            else:
                # return silent audio data until next source is ready
                return AudioSegment.silent(duration=20, frame_rate=48000).raw_data

        # calculate volume for fade in/out effect
        factor = min([time_elapsed, time_remaining])
        source.volume = (factor / (self.audio_fade_time * 1000)) * self.volume

        return source.read()


class YTDLSource(discord.PCMVolumeTransformer):
    """Wrapper over `discord.PCMVolumeTransformer` for the purpose of keeping audio data
    in memory. This gives us the option to download the file while streaming it to the
    client at the same time, without needing to fetch from YouTube twice.
    """

    # TODO: programmed this in mind that download functionality will always be used,
    # but should check to make it still works even without it
    # NOTE: because of the way we built this, it'll also be possible to detect any
    # issues with the stream before the bytes are actually getting read, so we have a
    # chance to repair audio streams and continue downloading if we only get like half
    # way through a download and an error occurs
    def __init__(
        self,
        source: discord.FFmpegPCMAudio,
        *,
        volume=1.0,
        loop: asyncio.AbstractEventLoop = None,
        metadata: Mapping[str, Any] = None,
        download=False,
    ):
        super().__init__(source, volume)
        self.source = source
        self.loop = loop or asyncio.get_event_loop()
        self.metadata = metadata
        self.is_stream_ready = False
        self.is_download_ready = False
        self._audio_buffer: List[bytes] = []
        self._audio_buffer_index = -1

        if download:
            self.download_task = self.loop.create_task(self.start_download())

    @classmethod
    async def from_query(
        cls, query: str, *, loop: asyncio.AbstractEventLoop = None, download=True
    ):
        """Instantiate `YTDLSource` from a generic query or URL."""
        logger.debug(f"Fetching metadata for query: {query}")
        start_time = perf_counter()

        ytdl = youtube_dl.YoutubeDL(YTDL_FORMAT_OPTIONS)
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(query, download=False)
        )
        if "entries" in data:
            data = data["entries"][0]

        end_time = perf_counter()
        logger.debug(
            f"Fetched metadata for query: {query} (took {end_time - start_time:0.2f} seconds)"
        )

        return cls(
            discord.FFmpegPCMAudio(data["url"], **ffmpeg_options),
            loop=loop,
            metadata=data,
            download=download
        )

    @classmethod
    def from_file(cls, filename: str | BufferedIOBase):
        return cls(
            discord.FFmpegPCMAudio(filename, **ffmpeg_options), data={"duration": 1}
        )

    async def wait_for_stream_ready_state(self):
        """Coroutine that resolves when the source is ready to start streaming."""
        while self.is_stream_ready is not True:
            await asyncio.sleep(0)
        return True

    async def wait_for_download_ready_state(self):
        """Coroutine that resolves when the source is fully downloaded."""
        while self.is_download_ready is not True:
            await asyncio.sleep(0)
        return True

    async def start_download(self):
        """Long running coroutine that starts downloading bytes from the audio source
        and keeps them in an internal buffer. Updates internal `is_stream_ready` state
        to `True` once the buffer has more than 1 second of audio data, and
        `is_download_ready` state to `True` once the audio has been fully downloaded.
        """
        title = self.metadata["title"]
        logger.debug(f"Starting download for: {title}")
        start_time = perf_counter()

        total_ms = 0
        while True:
            # 20ms worth of 16-bit 48KHz stereo PCM (about 3,840 bytes / frame)
            bytes = self.source.read()
            if bytes == b"":
                break
            total_ms += 20
            self._audio_buffer.append(bytes)

            if total_ms >= 1000:
                self.is_stream_ready = True

            await asyncio.sleep(0)

        self.is_download_ready = True

        end_time = perf_counter()
        logger.info(
            f"Finished downloading {title} with {len(self._audio_buffer)} total bytes "
            f"and {total_ms / 1000} seconds (took {end_time - start_time:0.2f} "
            "seconds)"
        )

    def prepare_filename(self):
        """Prepares a linux filesystem-compatible filename to be used by the current
        source download.
        """
        title = self.metadata['title'].replace("/", "")
        return title

    async def write_buffer_to_file(self, filename: str = None) -> str:
        """Writes the current audio buffer to a file. Internal `is_download_ready` state
        must be `True`.
        """
        if not self.is_download_ready:
            raise Exception("download not yet available")

        # NOTE: only replacing the '/' character since that is the only restricted
        # filename character on Linux
        title = self.metadata['title']
        filename = filename or f"downloads/{title.replace('/', '')}.mp3"
        logger.debug(f"Saving to {filename}")

        segment = AudioSegment(
            b"".join(self._audio_buffer),
            sample_width=2,
            frame_rate=48000,
            channels=2,
        )

        # NOTE: this works but has a chance to lag the playing audio stream
        filename = await self.loop.run_in_executor(
            None, lambda: segment.export(filename, format="mp3")
        )

        logger.debug(filename)

        return filename

    def get_progress(self) -> float:
        """Returns a float (0.0 through 1.0) indicating how much audio data has been
        read by the buffer.
        """
        if not self.is_stream_ready:
            raise Exception("stream not yet ready")

        if self._audio_buffer_index <= 0:
            return 0.0

        return self._audio_buffer_index + 1 / len(self._audio_buffer)

    def get_time_elapsed(self) -> float:
        """Returns number of miliseconds worth of audio data that has been read from the
        buffer.
        """
        return (self._audio_buffer_index + 1) * 20

    def get_time_remaining(self) -> float:
        """Returns number of miliseconds worth of audio data remaining in the audio
        buffer.
        """
        # TODO: adjust this to check the duration of the source, not the length of the
        # loaded buffer
        bytes_remaining = len(self._audio_buffer) - self._audio_buffer_index + 1
        return bytes_remaining * 20

    def read(self) -> bytes:
        if not self.is_stream_ready:
            raise Exception("stream not yet ready")

        if self._audio_buffer_index + 1 > len(self._audio_buffer):
            return b""

        self._audio_buffer_index += 1
        data = self._audio_buffer[self._audio_buffer_index]

        return data
