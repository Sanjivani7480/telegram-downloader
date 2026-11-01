import os
import asyncio
import glob
import yt_dlp

from urllib.parse import urlparse
from config import DOWNLOAD_DIR, FFMPEG_LOCATION, MAX_FILE_SIZE_MB

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

ALLOWED_DOMAINS = [
    "youtube.com",
    "youtu.be",
    "instagram.com",
    "facebook.com",
    "fb.watch",
    "twitter.com",
    "x.com",
]


def detect_platform(url):
    host = (urlparse(url).hostname or "").lower()

    if not any(
        host == domain or host.endswith("." + domain)
        for domain in ALLOWED_DOMAINS
    ):
        return None

    if "youtube.com" in host or host == "youtu.be":
        return "YouTube"

    if "instagram.com" in host:
        return "Instagram"

    if "facebook.com" in host or host == "fb.watch":
        return "Facebook"

    if "twitter.com" in host or host == "x.com":
        return "X (Twitter)"

    return None


def download_media(url):
    platform = detect_platform(url)

    if not platform:
        raise ValueError("Unsupported or invalid URL")

    options = {
        "format": (
            "best[filesize<45M]/"
            "best[filesize_approx<45M]/"
            "worst[filesize<45M]/worst"
        ),
        "outtmpl": os.path.join(
            DOWNLOAD_DIR, "%(id)s.%(ext)s"
        ),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "merge_output_format": "mp4",
        "ffmpeg_location": FFMPEG_LOCATION,
        "socket_timeout": 30,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)

    # Locate the downloaded file
    files = glob.glob(os.path.join(DOWNLOAD_DIR, "*"))

    if not files:
        raise RuntimeError("Download failed")

    # Use the most recently modified downloaded file
    filepath = max(files, key=os.path.getmtime)

    size_mb = os.path.getsize(filepath) / (1024 * 1024)

    if size_mb > MAX_FILE_SIZE_MB:
        os.remove(filepath)
        raise ValueError(
            f"File is too large ({size_mb:.1f} MB). "
            "Try a smaller quality or another link."
        )

    return filepath, info, platform


async def download_media_async(url):
    return await asyncio.to_thread(download_media, url)