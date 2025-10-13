import re

#FFmpeg
FFMPEG_BEFORE = (
    '-re -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 '
    '-analyzeduration 0 -probesize 32'
)
FFMPEG_OPTIONS = (
    '-vn -af "volume=0.06,aresample=async=1000:first_pts=0" '
    '-b:a 256k -bufsize 4M -maxrate 2M'
)

#Allowed domain
ALLOWED_BASE_DOMAINS = {
    "youtube.com",
    "youtu.be",
    "soundcloud.com",
    "nicovideo.jp",
    "x.com",
    "mixcloud.com",
    "twitch.tv",
}

#yt-dlp
YTDLP_INFO_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'ytsearch',
    'socket_timeout': 10,
    'retries': 5,
    'fragment_retries': 5,
    'skip_unavailable_fragments': True,
    'throttled_rate': '100K',
    'extractor_retries': 3,
    'ignoreerrors': True,
    'geo_bypass': True,
    'nocheckcertificate': True,
    'playlist_items': '1',
    'max_downloads': 1,
    'concurrent_fragment_downloads': 1,
    'quiet': True,
    'no_warnings': True,
}

YTDLP_STREAM_OPTS = dict(YTDLP_INFO_OPTS)
YTDLP_STREAM_OPTS.update({
    'socket_timeout': 15,
    'retries': 10,
    'fragment_retries': 10,
    'extractor_retries': 5,
})

#正規表現
WWW_RE = re.compile(r'^www\.')