import os
import asyncio
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import (
    init_db,
    add_user,
    get_user,
    get_all_users,
    set_allowed,
    set_blocked,
)

from permissions import is_admin, is_allowed

import yt_dlp


# =========================
# CONFIG
# =========================

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN not found in .env file")

if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID not found in .env file")

ADMIN_ID = int(ADMIN_ID)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    existing_user = get_user(user.id)

    # ADMIN
    if user.id == ADMIN_ID:

        add_user(
            user.id,
            user.username or "",
            user.first_name or "",
            is_allowed=1,
            is_admin=1
        )

        await update.message.reply_text(
            "👑 Welcome, Admin!\n\n"
            "🤖 Your Media Downloader Bot is online.\n\n"
            "🔐 Admin access: ACTIVE\n\n"
            "Use /admin to open the Admin Panel."
        )

        return

    # NEW USER
    if not existing_user:

        add_user(
            user.id,
            user.username or "",
            user.first_name or "",
            is_allowed=0,
            is_admin=0
        )

        await update.message.reply_text(
            "👋 Hello!\n\n"
            "🤖 Welcome to the Media Downloader Bot.\n\n"
            f"🆔 Your Telegram ID: {user.id}\n\n"
            "🔒 Your access is currently pending approval."
        )

        return

    # BLOCKED
    if existing_user[5] == 1:

        await update.message.reply_text(
            "🚫 Your access has been blocked."
        )

        return

    # ALLOWED
    if existing_user[3] == 1:

        await update.message.reply_text(
            "👋 Welcome back!\n\n"
            "✅ Your access is active.\n\n"
            "📥 Send me an Instagram, YouTube, "
            "TikTok, Pinterest or Twitter/X link."
        )

        return

    # PENDING
    await update.message.reply_text(
        "⏳ Your access is still pending approval.\n\n"
        "Please wait for the admin to approve your account."
    )


# =========================
# MY ID
# =========================

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    await update.message.reply_text(
        f"🆔 Your Telegram User ID is:\n\n{user.id}"
    )


# =========================
# ADMIN PANEL
# =========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if not is_admin(user.id):

        await update.message.reply_text(
            "❌ You don't have admin access."
        )

        return

    keyboard = [
        [
            InlineKeyboardButton(
                "👥 All Users",
                callback_data="all_users"
            ),
            InlineKeyboardButton(
                "✅ Allowed",
                callback_data="allowed_users"
            ),
        ],
        [
            InlineKeyboardButton(
                "🚫 Blocked",
                callback_data="blocked_users"
            ),
            InlineKeyboardButton(
                "⏳ Pending",
                callback_data="pending_users"
            ),
        ],
        [
            InlineKeyboardButton(
                "➕ Allow User",
                callback_data="allow_user"
            ),
            InlineKeyboardButton(
                "⛔ Block User",
                callback_data="block_user"
            ),
        ],
    ]

    await update.message.reply_text(
        "👑 ADMIN PANEL\n\n"
        "Select an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# ADMIN BUTTONS
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    if not is_admin(user_id):

        await query.edit_message_text(
            "❌ You don't have admin access."
        )

        return

    users = get_all_users()

    # ALL USERS
    if query.data == "all_users":

        if not users:

            text = "👥 No users found."

        else:

            text = "👥 ALL USERS\n\n"

            for user in users:

                uid, username, first_name, allowed, admin_status, blocked = user

                if admin_status:
                    status = "👑 Admin"

                elif blocked:
                    status = "🚫 Blocked"

                elif allowed:
                    status = "✅ Allowed"

                else:
                    status = "⏳ Pending"

                text += (
                    f"👤 {first_name or 'Unknown'}\n"
                    f"🆔 {uid}\n"
                    f"📱 @{username if username else 'No username'}\n"
                    f"Status: {status}\n\n"
                )

        await query.edit_message_text(text)

    # ALLOWED USERS
    elif query.data == "allowed_users":

        allowed_users = [
            u for u in users
            if u[3] == 1 and u[5] == 0
        ]

        if not allowed_users:

            text = "✅ No allowed users."

        else:

            text = "✅ ALLOWED USERS\n\n"

            for user in allowed_users:

                uid, username, first_name, allowed, admin_status, blocked = user

                text += (
                    f"👤 {first_name or 'Unknown'}\n"
                    f"🆔 {uid}\n"
                    f"📱 @{username if username else 'No username'}\n\n"
                )

        await query.edit_message_text(text)

    # BLOCKED USERS
    elif query.data == "blocked_users":

        blocked_users = [
            u for u in users
            if u[5] == 1
        ]

        if not blocked_users:

            text = "🚫 No blocked users."

        else:

            text = "🚫 BLOCKED USERS\n\n"

            for user in blocked_users:

                uid, username, first_name, allowed, admin_status, blocked = user

                text += (
                    f"👤 {first_name or 'Unknown'}\n"
                    f"🆔 {uid}\n"
                    f"📱 @{username if username else 'No username'}\n\n"
                )

        await query.edit_message_text(text)

    # PENDING USERS
    elif query.data == "pending_users":

        pending_users = [
            u for u in users
            if u[3] == 0 and u[4] == 0 and u[5] == 0
        ]

        if not pending_users:

            text = "⏳ No pending users."

        else:

            text = "⏳ PENDING USERS\n\n"

            for user in pending_users:

                uid, username, first_name, allowed, admin_status, blocked = user

                text += (
                    f"👤 {first_name or 'Unknown'}\n"
                    f"🆔 {uid}\n"
                    f"📱 @{username if username else 'No username'}\n\n"
                )

        await query.edit_message_text(text)

    # ALLOW USER
    elif query.data == "allow_user":

        context.user_data["waiting_for"] = "allow"

        await query.edit_message_text(
            "➕ ALLOW USER\n\n"
            "Send the Telegram User ID you want to allow.\n\n"
            "Example:\n"
            "123456789"
        )

    # BLOCK USER
    elif query.data == "block_user":

        context.user_data["waiting_for"] = "block"

        await query.edit_message_text(
            "⛔ BLOCK USER\n\n"
            "Send the Telegram User ID you want to block.\n\n"
            "Example:\n"
            "123456789"
        )


# =========================
# ADMIN USER ACTION
# =========================

async def handle_admin_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not is_admin(user.id):
        return

    action = context.user_data.get("waiting_for")

    if not action:
        return

    try:

        target_id = int(update.message.text.strip())

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid User ID.\n\n"
            "Please send only the numeric Telegram User ID."
        )

        return

    target_user = get_user(target_id)

    if not target_user:

        await update.message.reply_text(
            "❌ User not found in database.\n\n"
            "Ask that user to send /start first."
        )

        context.user_data.clear()

        return

    if action == "allow":

        set_allowed(target_id, True)
        set_blocked(target_id, False)

        await update.message.reply_text(
            "✅ User access granted!\n\n"
            f"🆔 User ID: {target_id}"
        )

    elif action == "block":

        set_blocked(target_id, True)
        set_allowed(target_id, False)

        await update.message.reply_text(
            "🚫 User blocked!\n\n"
            f"🆔 User ID: {target_id}"
        )

    context.user_data.clear()


# =========================
# DOWNLOAD MEDIA
# =========================

def download_media(url, folder):

    output_template = str(
        Path(folder) / "%(title)s_%(id)s.%(ext)s"
    )

    options = {
        "outtmpl": output_template,

        "format": "best[ext=mp4]/best",

        "noplaylist": True,

        "quiet": True,

        "no_warnings": True,

        "restrictfilenames": True,

        "writethumbnail": False,
    }

    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

        files = [
            p for p in Path(folder).iterdir()
            if p.is_file()
        ]

        if files:

            return files

        return []


# =========================
# PLATFORM DETECTION
# =========================

def detect_platform(url):

    url_lower = url.lower()

    if "instagram.com" in url_lower:
        return "📸 Instagram"

    if (
        "youtube.com" in url_lower
        or "youtu.be" in url_lower
    ):
        return "▶️ YouTube"

    if "tiktok.com" in url_lower:
        return "🎵 TikTok"

    if (
        "pinterest.com" in url_lower
        or "pin.it" in url_lower
    ):
        return "📌 Pinterest"

    if (
        "twitter.com" in url_lower
        or "x.com" in url_lower
    ):
        return "🐦 Twitter / X"

    return "🌐 Media"


# =========================
# SEND MEDIA
# =========================

async def send_media_files(
    update,
    files,
    platform
):

    sent_count = 0

    for file_path in files:

        file_path = Path(file_path)

        if not file_path.exists():
            continue

        extension = file_path.suffix.lower()

        try:

            # VIDEO
            if extension in [
                ".mp4",
                ".mov",
                ".mkv",
                ".webm",
                ".avi"
            ]:

                with open(file_path, "rb") as media:

                    await update.message.reply_video(
                        video=media,
                        caption=(
                            f"✅ Downloaded successfully!\n\n"
                            f"{platform}"
                        ),
                        supports_streaming=True
                    )

                sent_count += 1

            # IMAGE
            elif extension in [
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            ]:

                with open(file_path, "rb") as media:

                    await update.message.reply_photo(
                        photo=media,
                        caption=(
                            f"✅ Downloaded successfully!\n\n"
                            f"{platform}"
                        )
                    )

                sent_count += 1

        except Exception as e:

            print(
                f"Could not send {file_path}:",
                repr(e)
            )

    return sent_count


# =========================
# SOCIAL MEDIA LINK
# =========================

async def handle_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    # Admin action
    if (
        is_admin(user.id)
        and context.user_data.get("waiting_for")
    ):

        await handle_admin_action(
            update,
            context
        )

        return

    # Permission
    if not is_allowed(user.id):

        await update.message.reply_text(
            "🔒 You don't have download access yet.\n\n"
            "Please wait for the admin to approve your account."
        )

        return

    url = update.message.text.strip()

    # URL check
    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):

        await update.message.reply_text(
            "❌ Please send a valid social media link."
        )

        return

    platform = detect_platform(url)

    processing_message = await update.message.reply_text(
        f"{platform}\n\n"
        "🔎 Searching for your media..."
    )

    try:

        # =========================
        # DOWNLOAD
        # =========================

        with tempfile.TemporaryDirectory() as temp_folder:

            files = await asyncio.to_thread(
                download_media,
                url,
                temp_folder
            )

            if not files:

                await processing_message.edit_text(
                    "❌ Media not found.\n\n"
                    "The link may be private, invalid "
                    "or unsupported."
                )

                return

            await processing_message.edit_text(
                f"{platform}\n\n"
                "📤 Media found!\n"
                "Sending to Telegram..."
            )

            sent_count = await send_media_files(
                update,
                files,
                platform
            )

            if sent_count == 0:

                await processing_message.edit_text(
                    "❌ I found the media, but Telegram "
                    "couldn't send this file type."
                )

                return

            await processing_message.delete()

    except Exception as e:

        print(
            "Download error:",
            repr(e)
        )

        try:
            await processing_message.edit_text(
                "❌ Download failed.\n\n"
                "The link may be private, "
                "unsupported, or temporarily unavailable."
            )

        except Exception:
            pass


# =========================
# MAIN
# =========================

def main():

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "myid",
            myid
        )
    )

    app.add_handler(
        CommandHandler(
            "admin",
            admin
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_link
        )
    )

    print("🤖 Bot is starting...")
    print("✅ Bot is running. Press Ctrl+C to stop.")

    app.run_polling()


if __name__ == "__main__":
    main()