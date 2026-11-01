import os
import re
import logging
import shutil
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile, Update

from config import BOT_TOKEN
from downloader import detect_platform, download_media_async

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not WEBHOOK_SECRET:
    raise RuntimeError("WEBHOOK_SECRET is missing")

if not RENDER_EXTERNAL_URL:
    raise RuntimeError("RENDER_EXTERNAL_URL is missing")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Welcome to YT / Insta / Twitter Downloader!\n\n"
        "📥 Send me a supported public media link.\n\n"
        "Supported platforms:\n"
        "▶️ YouTube\n"
        "📸 Instagram\n"
        "📘 Facebook\n"
        "🐦 X (Twitter)\n\n"
        "Commands:\n"
        "/start - Start bot\n"
        "/help - Help"
    )


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "Send a supported public YouTube, Instagram, "
        "Facebook or X media URL.\n\n"
        "Only submit content you own or have permission to download."
    )


@dp.message(F.text)
async def process_link(message: Message):
    url = message.text.strip()

    if not re.fullmatch(r"https?://\S+", url):
        await message.answer("❌ Please send a valid media URL.")
        return

    if not detect_platform(url):
        await message.answer(
            "❌ Unsupported platform.\n\n"
            "Supported: YouTube, Instagram, Facebook and X."
        )
        return

    status = await message.answer("⏳ Processing your link. Please wait.")

    filepath = None
    folder = None

    try:
        result = await download_media_async(url)

        # Support either a 3-item or 4-item downloader result.
        if len(result) == 4:
            filepath, folder, info, platform = result
        elif len(result) == 3:
            filepath, info, platform = result
        else:
            raise ValueError("Unexpected result from download_media_async")

        if not filepath or not os.path.isfile(filepath):
            raise FileNotFoundError("Downloaded file was not found")

        await status.edit_text(
            f"✅ Download completed!\nPlatform: {platform}\nSending media..."
        )

        filename = os.path.basename(filepath)
        media = FSInputFile(filepath, filename=filename)
        extension = Path(filepath).suffix.lower()

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

    except Exception:
        logger.exception("Download error")
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
        if folder and os.path.isdir(folder):
            shutil.rmtree(folder, ignore_errors=True)
        elif filepath and os.path.isfile(filepath):
            os.remove(filepath)


async def handle_webhook(request: web.Request):
    secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if secret != WEBHOOK_SECRET:
        raise web.HTTPUnauthorized(text="Invalid webhook secret")

    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception:
        logger.exception("Webhook update processing failed")
        raise web.HTTPBadRequest(text="Invalid update")

    return web.Response(text="OK")


async def health(request: web.Request):
    return web.Response(text="Telegram Downloader is running!")


async def on_startup(app: web.Application):
    webhook_url = RENDER_EXTERNAL_URL.rstrip("/") + "/webhook"

    await bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True
    )

    logger.info("Webhook registered: %s", webhook_url)


async def on_cleanup(app: web.Application):
    await bot.session.close()


def main():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_post("/webhook", handle_webhook)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()