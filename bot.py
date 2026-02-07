# -*- coding: utf-8 -*-
import telebot
import time
import json
import os
from telebot import types

# تنظیمات ربات
TOKEN = os.getenv("BOT_TOKEN")  # توکن از Secret خوانده می‌شود
YOUR_CHAT_ID = "1761692934"

# ایجاد ربات
bot = telebot.TeleBot(TOKEN)

# ساختارهای داده
recent_messages = []  # پیام‌های اخیر
MAX_MESSAGES = 50  # حداکثر تعداد پیام ذخیره شده
reply_sessions = {}  # {admin_id: {'target_user_id': X, 'target_message_id': Y, 'status': ''}}

# فایل ذخیره داده‌ها
DATA_FILE = "bot_data.json"

print("🤖 ربات پیام‌رسان با قابلیت ریپلای فعال شد!")
print(f"🆔 آیدی شما: {YOUR_CHAT_ID}")
print("📱 منتظر پیام کاربران...")

# === توابع کمکی ===
def save_data():
    """ذخیره داده‌ها در فایل"""
    data = {
        'recent_messages': recent_messages,
        'reply_sessions': reply_sessions
    }
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره داده‌ها: {e}")

def load_data():
    """بارگذاری داده‌ها از فایل"""
    global recent_messages, reply_sessions
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                recent_messages = data.get('recent_messages', [])
                reply_sessions = data.get('reply_sessions', {})
                print(f"✅ داده‌ها بارگذاری شد: {len(recent_messages)} پیام")
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری داده‌ها: {e}")

# بارگذاری داده‌های قبلی
load_data()

# === دکمه‌های ریپلای ===
def create_reply_keyboard(user_id, message_id):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn_reply = types.InlineKeyboardButton(
        text="📩 ریپلای به کاربر",
        callback_data=f"reply_{user_id}_{message_id}"
    )
    btn_cancel = types.InlineKeyboardButton(
        text="❌ لغو ریپلای",
        callback_data="cancel_reply"
    )
    keyboard.add(btn_reply, btn_cancel)
    return keyboard

def create_cancel_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(
        text="❌ انصراف از ارسال",
        callback_data="cancel_send"
    )
    keyboard.add(btn)
    return keyboard

# === هندلر اصلی برای کاربران ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        welcome_text = """
👋 *سلام!*

این ربات پیام‌رسان است. هر پیامی که بفرستید:
1️⃣ برای صاحب ربات ارسال می‌شود
2️⃣ تأییدیه دریافت به شما نمایش داده می‌شود

✍️ *کافیه پیام خود را بنویسید*

⚠️ *پیام‌ها به صورت ناشناس ارسال می‌شوند*
"""
        bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')

        # اطلاع به شما از کاربر جدید
        user_info = f"""
👤 *کاربر جدید:*
نام: {message.from_user.first_name}
یوزرنیم: @{message.from_user.username if message.from_user.username else 'ندارد'}
آیدی: `{message.from_user.id}`
"""
        msg = bot.send_message(YOUR_CHAT_ID, user_info, parse_mode='Markdown')
        bot.edit_message_reply_markup(
            chat_id=YOUR_CHAT_ID,
            message_id=msg.message_id,
            reply_markup=create_reply_keyboard(message.from_user.id, msg.message_id)
        )
    except Exception as e:
        print(f"⚠️ خطا در send_welcome: {e}")

# === هندلر پیام کاربران غیر ادمین ===
@bot.message_handler(func=lambda message: str(message.from_user.id) != YOUR_CHAT_ID)
def forward_user_message(message):
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        username = f"@{message.from_user.username}" if message.from_user.username else "بدون یوزرنیم"
        user_text = message.text

        if user_text.startswith('/'):
            return

        print(f"📩 پیام جدید از {user_name}: {user_text[:50]}...")

        forward_info = f"""
📬 *پیام جدید از کاربر:*

👤 نام: {user_name}
🆔 آیدی: `{user_id}`
📝 یوزرنیم: {username}

✉️ *پیام:*
{user_text}

⏰ زمان: {time.strftime('%H:%M:%S')}
"""
        msg_to_admin = bot
.send_message(
            YOUR_CHAT_ID,
            forward_info,
            parse_mode='Markdown',
            reply_markup=create_reply_keyboard(user_id, message.message_id)
        )

        recent_messages.append({
            'user_id': user_id,
            'user_name': user_name,
            'text': user_text,
            'time': time.time(),
            'user_message_id': message.message_id,
            'admin_message_id': msg_to_admin.message_id
        })

        if len(recent_messages) > MAX_MESSAGES:
            recent_messages.pop(0)

        confirmation = f"""
✅ *پیام شما ارسال شد!*

متن شما:
"{user_text[:100]}{'...' if len(user_text) > 100 else ''}"

🔄 برای ارسال پیام جدید، کافیست بنویسید.
"""
        bot.reply_to(message, confirmation, parse_mode='Markdown')
        save_data()

    except Exception as e:
        print(f"❌ خطا در forward_user_message: {e}")
        bot.reply_to(message, "❌ متأسفانه خطایی در ارسال پیام رخ داد.")

# === هندلر callback دکمه‌ها ===
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        admin_id = str(call.from_user.id)
        if admin_id != YOUR_CHAT_ID:
            bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
            return

        # ریپلای به کاربر
        if call.data.startswith('reply_'):
            parts = call.data.split('_')
            if len(parts) >= 3:
                target_user_id = parts[1]
                target_message_id = parts[2] if len(parts) > 2 else None
                reply_sessions[admin_id] = {
                    'target_user_id': target_user_id,
                    'target_message_id': target_message_id,
                    'status': 'waiting_for_reply'
                }

                guide_text = f"✍️ در حال پاسخ به کاربر..."
                cancel_msg = bot.send_message(
                    YOUR_CHAT_ID,
                    guide_text,
                    reply_markup=create_cancel_keyboard()
                )
                reply_sessions[admin_id]['cancel_message_id'] = cancel_msg.message_id
                bot.answer_callback_query(call.id, "📝 لطفا پاسخ خود را بنویسید")

        elif call.data == 'cancel_reply':
            if admin_id in reply_sessions:
                del reply_sessions[admin_id]
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
            bot.answer_callback_query(call.id, "✅ ریپلای لغو شد")

        elif call.data == 'cancel_send':
            if admin_id in reply_sessions:
                try:
                    bot.delete_message(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id
                    )
                except:
                    pass
                del reply_sessions[admin_id]
            bot.answer_callback_query(call.id, "✅ ارسال پیام لغو شد")

        save_data()

    except Exception as e:
        print(f"❌ خطا در callback: {e}")
        try:
            bot.answer_callback_query(call.id, "❌ خطایی رخ داد")
        except:
            pass

# === پیام ادمین ===
@bot.message_handler(func=lambda message: str(message.from_user.id) == YOUR_CHAT_ID)
def handle_admin_message(message):
    try:
        admin_id = str(message.from_user.id)
        if admin_id in reply_sessions and reply_sessions[admin_id].get('status') == 'waiting_for_reply':
            handle_admin_reply(message)
        else:
            handle_admin_command(message)
    except Exception as e:
        print(f"❌ خطا در handle_admin_message: {e}")

def handle_admin_reply(message):
    try:
        admin_id = str(message.from_user.id)
        session = reply_sessions[admin_id]
        target_user_id = session['target_user_id']
        reply_text = message.text

        if reply_text.startswith('/'):
            handle_admin_command(message)
            return

        user_name = "
کاربر"
        for msg in recent_messages:
            if str(msg['user_id']) == target_user_id:
                user_name = msg['user_name']
                break

        user_response = f"""
📨 *پاسخ از صاحب ربات:*

{reply_text}

🔄 برای پاسخ مجدد، پیام جدید بنویسید.
"""
        bot.send_message(target_user_id, user_response, parse_mode='Markdown')

        success_msg = f"""
✅ *پاسخ شما ارسال شد!*

به: {user_name}
آیدی: `{target_user_id}`

📝 متن پاسخ:
{reply_text}
"""
        bot.reply_to(message, success_msg, parse_mode='Markdown')

        if 'cancel_message_id' in session:
            try:
                bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=session['cancel_message_id']
                )
            except:
                pass

        del reply_sessions[admin_id]

        for msg in recent_messages:
            if str(msg['user_id']) == target_user_id:
                try:
                    bot.edit_message_text(
                        chat_id=YOUR_CHAT_ID,
                        message_id=msg.get('admin_message_id'),
                        text=f"✅ *پاسخ داده شده*\n\n{message.text}",
                        parse_mode='Markdown',
                        reply_markup=None
                    )
                except:
                    pass
                break

        save_data()

    except Exception as e:
        print(f"❌ خطا در handle_admin_reply: {e}")
        bot.reply_to(message, f"❌ خطا در ارسال پاسخ: {e}")
        if admin_id in reply_sessions:
            del reply_sessions[admin_id]

def handle_admin_command(message):
    admin_id = str(message.from_user.id)
    text = message.text

    if text == '/admin':
        admin_text = """
🛠 *دستورات ادمین:*

/stats - آمار ربات
/recent - آخرین پیام‌ها
/clear - پاک کردن پیام‌های ذخیره شده
/cancel - لغو ریپلای فعلی

💡 برای ریپلای: روی دکمه "ریپلای به کاربر" کلیک کنید
"""
        bot.reply_to(message, admin_text, parse_mode='Markdown')

    elif text == '/stats':
        active_reply = "✅ فعال" if admin_id in reply_sessions else "❌ غیرفعال"
        stats_text = f"""
📊 *آمار ربات:*

پیام‌های ذخیره شده: {len(recent_messages)}
حداکثر ذخیره: {MAX_MESSAGES}
وضعیت ریپلای: {active_reply}

برای دیدن پیام‌ها: /recent
"""
        bot.reply_to(message, stats_text, parse_mode='Markdown')

    elif text == '/recent':
        if not recent_messages:
            bot.reply_to(message, "📭 هیچ پیامی ذخیره نشده است")
            return

        recent_text = "📨 *آخرین 10 پیام:*\n\n"
        for i, msg in enumerate(recent_messages[-10:], 1):
            recent_text += f"{i}. {msg['user_name']} (آیدی: `{msg['user_id']}`): {msg['text'][:40]}...\n"
        bot.reply_to(message, recent_text, parse_mode='Markdown')

    elif text == '/clear':
        recent_messages.clear()
        save_data()
        bot.reply_to(message, "✅ همه پیام‌های ذخیره شده پاک شدند")

    elif text == '/cancel':
        if admin_id in reply_sessions:
            del reply_sessions[admin_id]
            save_data()
            bot.reply_to(message, "✅ ریپلای فعلی لغو شد")
        else:
            bot.reply_to(message, "⚠️ وضعیت ریپلای فعالی وجود ندارد")

    else:
        bot.reply_to(message, "💡 برای پاسخ به کاربران، روی دکمه 'ریپلای به کاربر' کلیک کنید.")

# === رسانه از کاربران ===
@bot.message_handler(content_types=['photo', 'video', 'document', 'voice'])
def forward_media(message):
    if str(message.from_user.id) == YOUR_CHAT_ID:
        return

    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name

        bot.forward_message(YOUR_CHAT_ID, message.chat.id, message.message_id)

        media_type = {
            'photo': 'عکس',
            'video': 'ویدیو',
            'document': 'فایل',
            'voice': 'ویس'
        }.get(message.content_type, 'رسانه')

        info = f"📎 {media_type} جدید از {user_name} (آیدی: {user_id})"
        msg = bot.send_message(YOUR_CHAT_ID, info, reply_markup=
create_reply_keyboard(user_id, message.message_id))

        recent_messages.append({
            'user_id': user_id,
            'user_name': user_name,
            'text': f"[{media_type}]",
            'time': time.time(),
            'user_message_id': message.message_id,
            'admin_message_id': msg.message_id
        })

        bot.reply_to(message, f"✅ {media_type} شما ارسال شد!")
        save_data()

    except Exception as e:
        print(f"❌ خطا در ارسال رسانه: {e}")
        bot.reply_to(message, f"❌ خطا در ارسال رسانه")

# === اجرای ربات ===
def run_bot():
    while True:
        try:
            print("🔄 در حال اتصال به سرور تلگرام...")
            bot.polling(none_stop=True, interval=2, timeout=30)
        except Exception as e:
            print(f"⚠️ خطا در اتصال: {e}")
            print("⏳ 5 ثانیه دیگر تلاش مجدد...")
            time.sleep(5)
            save_data()

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n👋 ربات متوقف شد. ذخیره داده‌ها...")
        save_data()
