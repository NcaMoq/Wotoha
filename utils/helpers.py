import asyncio
import logging
from urllib.parse import urlparse
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

import yt_dlp
from discord import FFmpegOpusAudio

from config import (
    ALLOWED_BASE_DOMAINS, WWW_RE, YTDLP_STREAM_OPTS, FFMPEG_BEFORE, FFMPEG_OPTIONS
)

logger = logging.getLogger("wotoha.helpers")

stream_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="stream_worker")
STREAM_YTDL = yt_dlp.YoutubeDL(YTDLP_STREAM_OPTS)


@lru_cache(maxsize=512)
def is_allowed_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.split("@")[-1]
        domain = domain.split(":")[0]
    except Exception:
        return False

    domain = WWW_RE.sub("", domain.lower())

    for base in ALLOWED_BASE_DOMAINS:
        if domain == base or domain.endswith("." + base):
            return True
    return False

async def extract_full_info(url: str) -> dict:
    loop = asyncio.get_event_loop()
    try:
        info = await loop.run_in_executor(
            stream_executor,
            lambda: STREAM_YTDL.extract_info(url, download=False)
        )
        if not info:
            raise RuntimeError("Could not fetch video information")
        
        return {
            'title': info.get('title', 'Unknown Title'),
            'webpage_url': info.get('webpage_url'),
            'thumbnail': info.get('thumbnail'),
            'uploader': info.get('uploader'),
            'duration': info.get('duration') or 0,
            'view_count': info.get('view_count') or 0,
            'stream_url': info.get('url'),
            'original_url': url,
        }
    except Exception as e:
        try:
            domain = urlparse(url).netloc.split(":")[0]
        except Exception:
            domain = "<unknown>"
        logger.warning("Failed to extract info from domain=%s: %s", domain, type(e).__name__)
        raise

async def prepare_audio_source(info: dict) -> FFmpegOpusAudio:
    if not info.get('stream_url'):
        full = await extract_full_info(info['original_url'])
        info['stream_url'] = full.get('stream_url')

    if not info.get('stream_url'):
        raise RuntimeError("Could not obtain stream URL")

    return FFmpegOpusAudio(
        info['stream_url'],
        pipe=False,
        before_options=FFMPEG_BEFORE,
        options=FFMPEG_OPTIONS
    )

async def set_bot_nickname(guild, nickname):
    try:
        if guild is None:
            return
        await guild.me.edit(nick=nickname)
    except discord.Forbidden:
        logger.debug("No permission to change nickname in guild %s", getattr(guild, "id", "<unknown>"))
    except Exception:
        logger.debug("Failed to change nickname (ignored)")