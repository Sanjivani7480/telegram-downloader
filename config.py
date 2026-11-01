import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().with_name(".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "45"))
FFMPEG_LOCATION = os.getenv(
    "FFMPEG_LOCATION",
    r"D:\Downloads\ffmpeg-9.0.2-essentials_build\ffmpeg-9.0.2-essentials_build\bin",
)

DOWNLOAD_DIR = "downloads"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing in .env file")