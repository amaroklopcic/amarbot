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
class YTDLSourcesManager:
    # number of seconds before and after the track to fade in/out the audio
    audio_fade_seconds = 5

    # TODO: add a user defined volume and fade in/out to that volume instead of 1
    def __init__(self) -> None:
        self.sources: List[YTDLSource] = []
        self.current_source_index = 0
        self.is_ready = False

    def read(self):
        if not self.is_ready:
            raise Exception("stream not yet ready")

        source = self.sources[self.current_source_index]
        time_elapsed = source.get_time_elapsed()
        time_remaining = source.get_time_remaining()
        # TODO: add volume fade in/out
        # TODO: add source transitions
        # if time_remaining <= 5.0:
        #     self.current_source_index += 1
        #     source = self.sources[self.current_source_index]

        return source.read()


class YTDLSource(discord.PCMVolumeTransformer):
    """Wrapper over `discord.PCMVolumeTransformer` for the purpose of keeping audio data
    in memory. This gives us the option to download the file while streaming it to the
    client at the same time, without needing to fetch from YouTube twice.
    """

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
    async def from_query(cls, query: str, *, loop: asyncio.AbstractEventLoop = None):
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

        end_time = perf_counter()
        logger.info(
            f"Finished downloading {title} with {len(self._audio_buffer)} total bytes "
            f"and {total_ms / 1000} seconds (took {end_time - start_time:0.2f} "
            "seconds)"
        )

    def write_buffer_to_file(self, filename: str = None) -> str:
        """Writes the current audio buffer to a file. Internal `is_stream_ready` state
        must be `True`.
        """
        if not self.is_download_ready:
            raise Exception("download not yet available")

        # TODO: sanitize filename -> lowercase + remove special chars
        filename = filename or f"downloads/{self.metadata['id']}.mp3"
        logger.debug(f"Saving to downloads directory...")
        segment = AudioSegment(
            self._audio_buffer.copy(),
            sample_width=2,
            frame_rate=48000,
            channels=2,
        )
        segment.export(filename, format="mp3")
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
        raise NotImplementedError()

    def get_time_remaining(self) -> float:
        """Returns number of miliseconds worth of audio data remaining in the audio
        buffer.
        """
        bytes_remaining = len(self._audio_buffer) - self._audio_buffer_index + 1
        return bytes_remaining * 20

    def read(self) -> bytes:
        if not self.is_stream_ready:
            raise Exception("stream not yet ready")

        self._audio_buffer_index += 1
        data = self._audio_buffer[self._audio_buffer_index]

        return data
