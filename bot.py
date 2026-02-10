# -*- coding: utf-8 -*-
import sys
import importlib

# کش‌باستر قبل از هر چیزی
def clear_python_cache():
    """پاک کردن کش پایتون"""
    modules_to_keep = ['sys', 'importlib', 'builtins', '__main__']
    for module_name in list(sys.modules.keys()):
        if module_name in modules_to_keep:
            continue
        if module_name.startswith('telebot') or module_name.startswith('telegram'):
            del sys.modules[module_name]
    print("✅ کش پایتون پاک شد")

clear_python_cache()
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = "8511185751:AAHpc-PTFtCNyBGrSknSKHv_6iV2O3Rdy4U"
ADMIN_ID = 1761692934  # آیدی عددی خودت

blocked_users = set()
reply_mode = {}

# ---------- User Message ----------
async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id in blocked_users:
        return

    info = (
        f"📩 پیام جدید\n\n"
        f"🆔 ID: {user.id}\n"
        f"👤 Username: @{user.username}\n"
        f"🧑 Name: {user.first_name} {user.last_name}\n"
        f"🌐 Language: {user.language_code}\n\n"
        f"💬 Message:\n{update.message.text}"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✉️ Reply", callback_data=f"reply:{user.id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
            InlineKeyboardButton("🚫 Block", callback_data=f"block:{user.id}")
        ]
    ])

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=info,
        reply_markup=keyboard
    )

# ---------- Button Handler ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("reply:"):
        user_id = int(data.split(":")[1])
        reply_mode[query.from_user.id] = user_id
        await query.message.reply_text(
            f"✍️ در حال ریپلای به کاربر {user_id}\nپیامتو بفرست:"
        )

    elif data.startswith("block:"):
        user_id = int(data.split(":")[1])
        blocked_users.add(user_id)
        await query.message.reply_text("🚫 کاربر بلاک شد")

    elif data == "cancel":
        reply_mode.pop(query.from_user.id, None)
        await query.message.reply_text("❌ ریپلای لغو شد")

# ---------- Admin Reply ----------
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id

    if admin_id not in reply_mode:
        return

    user_id = reply_mode[admin_id]

    if user_id in blocked_users:
        await update.message.reply_text("❌ کاربر بلاک است")
        return

    await context.bot.send_message(
        chat_id=user_id,
        text=update.message.text
    )

    await update.message.reply_text("✅ پیام ارسال شد")

# ---------- Unblock Command ----------
async def unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❗ استفاده:\n/unblock USER_ID")
        return

    user_id = int(context.args[0])
    blocked_users.discard(user_id)
    await update.message.reply_text(f"✅ کاربر {user_id} آنبلاک شد")

# ---------- Main ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("unblock", unblock))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), admin_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.User(ADMIN_ID), user_message))

    app.run_polling()

if __name__ == "__main__":
    main()
