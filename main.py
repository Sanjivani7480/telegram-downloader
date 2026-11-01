import os
import re
import logging
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    FSInputFile,
)

from config import BOT_TOKEN
from downloader import (
    detect_platform,
    download_media_async,
)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):

    welcome = """
👋 Welcome to YT / Insta / Twitter Downloader!

📥 Send me a supported public media link.

Supported platforms:

▶️ YouTube
📸 Instagram
📘 Facebook
🐦 X (Twitter)

I will try to download the available media
and send it directly here.

Commands:
/start - Start bot
/help - Help
"""

    await message.answer(welcome)


@dp.message(Command("help"))
async def help_command(message: Message):

    await message.answer(
        "Send a supported public YouTube, Instagram, "
        "Facebook or X media URL.\n\n"
        "Only content you own or have permission to "
        "download should be submitted."
    )


@dp.message(F.text)
async def process_link(message: Message):

    url = message.text.strip()

    # Accept only a single URL, not arbitrary text
    if not re.fullmatch(r"https?://\S+", url):
        await message.answer(
            "❌ Please send a valid media URL."
        )
        return

    if not detect_platform(url):
        await message.answer(
            "❌ Unsupported platform.\n\n"
            "Supported: YouTube, Instagram, Facebook and X."
        )
        return

    status = await message.answer(
        "⏳ Processing your link...\n"
        "Please wait."
    )

    filepath = None

    try:
        filepath, info, platform = await download_media_async(url)

        await status.edit_text(
            f"✅ Download completed!\n"
            f"Platform: {platform}\n"
            f"Sending your media..."
        )

        filename = os.path.basename(filepath)

        media = FSInputFile(
            filepath,
            filename=filename
        )

        extension = os.path.splitext(filepath)[1].lower()

        if extension in [".jpg", ".jpeg", ".png", ".webp"]:
            await message.answer_photo(
                photo=media,
                caption="📸 Media downloaded successfully!"
            )

        elif extension in [".mp4", ".mov", ".m4v"]:
            await message.answer_video(
                video=media,
                caption="🎬 Video downloaded successfully!",
                supports_streaming=True
            )

        else:
            await message.answer_document(
                document=media,
                caption="📥 Your downloaded media"
            )

        await status.delete()

    except Exception as e:

        logging.exception("Download error")

        await status.edit_text(
            "❌ Unable to download this media.\n\n"
            "Possible reasons:\n"
            "• Private or restricted content\n"
            "• Unsupported link\n"
            "• Platform restrictions\n"
            "• File too large\n\n"
            "Please try another permitted public link."
        )

    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)


async def main():

    print("Telegram Downloader Bot is running!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())