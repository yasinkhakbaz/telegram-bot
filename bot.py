#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 ربات پیام‌رسان تلگرام
کاربر → ربات → ادمین ↔ کاربر
"""

import telebot
import time
import json
import os
from datetime import datetime
from telebot import types

# ============ تنظیمات ============
TOKEN = "8511185751:AAHpc-PTFtCNyBGrSknSKHv_6iV2O3Rdy4U"  # از @BotFather
ADMIN_ID = "1761692934"               # از @userinfobot
# =================================

bot = telebot.TeleBot(TOKEN)

# ذخیره داده‌ها
messages_db = []
active_replies = {}  # {admin_id: target_user_id}

print("=" * 50)
print("🤖 ربات پیام‌رسان تلگرام")
print(f"👤 آیدی ادمین: {ADMIN_ID}")
print("🟢 ربات فعال و آماده است!")
print("=" * 50)

# ============ تابع‌های کمکی ============
def save_to_file():
    """ذخیره داده‌ها در فایل"""
    try:
        data = {
            'messages': messages_db[-100:],  # آخرین ۱۰۰ پیام
            'active_replies': active_replies
        }
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

def load_from_file():
    """بارگذاری داده‌ها از فایل"""
    global messages_db, active_replies
    try:
        if os.path.exists('data.json'):
            with open('data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                messages_db = data.get('messages', [])
                active_replies = data.get('active_replies', {})
                print(f"📂 {len(messages_db)} پیام بارگذاری شد")
    except:
        print("📂 شروع جدید")

load_from_file()

# ============ دکمه‌های اینلاین ============
def reply_buttons(user_id, msg_id):
    """دکمه‌های پاسخ برای ادمین"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📩 پاسخ", callback_data=f"reply_{user_id}_{msg_id}")
    btn2 = types.InlineKeyboardButton("👁️ مشاهده", callback_data=f"view_{user_id}")
    markup.add(btn1, btn2)
    return markup

def cancel_button():
    """دکمه لغو"""
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("❌ لغو پاسخ", callback_data="cancel_reply")
    markup.add(btn)
    return markup

# ============ دستورات ============
@bot.message_handler(commands=['start', 'help'])
def start_command(message):
    """دستور start"""
    name = message.from_user.first_name or "کاربر"
    
    welcome = f"""
    سلام {name}! 👋

    🤖 *ربات پیام‌رسان*

    ✍️ هر پیامی بفرستی، مستقیم به صاحب ربات می‌رسه.
    ✅ تأییدیه هم دریافت می‌کنی.

    فقط بنویس و ارسال کن!
    """
    
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown')
    
    # اطلاع به ادمین
    if str(message.from_user.id) != ADMIN_ID:
        try:
            notify = f"""
            👤 کاربر جدید:
            نام: {name}
            آیدی: `{message.from_user.id}`
            زمان: {datetime.now().strftime("%H:%M")}
            """
            bot.send_message(ADMIN_ID, notify, parse_mode='Markdown')
        except:
            pass

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """پنل ادمین"""
    if str(message.from_user.id) != ADMIN_ID:
        bot.reply_to(message, "❌ دسترسی ندارید!")
        return
    
    panel = """
    🛠️ *پنل ادمین*
    
    📊 /stats - آمار ربات
    📨 /recent - آخرین پیام‌ها
    🗑️ /clear - پاک کردن همه پیام‌ها
    ❌ /cancel - لغو پاسخ فعلی
    
    💡 برای پاسخ: روی دکمه "📩 پاسخ" کلیک کنید
    """
    bot.send_message(message.chat.id, panel, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats_command(message):
    """آمار ربات"""
    if str(message.from_user.id) != ADMIN_ID:
        return
    
    stats = f"""
    📊 *آمار ربات*
    
    کاربران منحصر به فرد: {len(set(m['user_id'] for m in messages_db))}
    کل پیام‌ها: {len(messages_db)}
    وضعیت: {'🟢 آنلاین' if ADMIN_ID not in active_replies else '✍️ در حال پاسخ'}
    """
    bot.reply_to(message, stats, parse_mode='Markdown')

@bot.message_handler(commands=['recent'])
def recent_messages(message):
    """آخرین پیام‌ها"""
    if str(message.from_user.id) != ADMIN_ID:
        return
    
    if not messages_db:
        bot.reply_to(message, "📭 هیچ پیامی وجود ندارد")
        return
    
    recent = "📨 *آخرین ۵ پیام:*\n\n"
    for msg in messages_db[-5:]:
        time_str = datetime.fromtimestamp(msg['time']).strftime("%H:%M")
        recent += f"• {msg['user_name']} ({time_str}): {msg['text'][:30]}...\n"
    
    bot.reply_to(message, recent, parse_mode='Markdown')

@bot.message_handler(commands=['clear'])
def clear_messages(message):
    """پاک کردن پیام‌ها"""
    if str(message.from_user.id) != ADMIN_ID:
        return
    
    messages_db.clear()
    save_to_file()
    bot.reply_to(message, "✅ همه پیام‌ها پاک شدند")

@bot.message_handler(commands=['cancel'])
def cancel_reply(message):
    """لغو پاسخ"""
    if str(message.from_user.id) != ADMIN_ID:
        return
    
    if ADMIN_ID in active_replies:
        del active_replies[ADMIN_ID]
        bot.reply_to(message, "✅ پاسخ لغو شد")
    else:
        bot.reply_to(message, "⚠️ وضعیت پاسخ فعالی وجود ندارد")

# ============ پیام از کاربران ============
@bot.message_handler(func=lambda m: str(m.from_user.id) != ADMIN_ID and not m.text.startswith('/'))
def handle_user_message(message):
    """پردازش پیام کاربران"""
    user = message.from_user
    text = message.text
    
    print(f"📩 پیام از {user.first_name}: {text[:50]}...")
    
    try:
        # ساخت پیام برای ادمین
        msg_for_admin = f"""
        📬 *پیام جدید*
        
        👤: {user.first_name}
        🆔: `{user.id}`
        ⏰: {datetime.now().strftime("%H:%M")}
        
        ✉️:
        {text}
        """
        
        # ارسال به ادمین با دکمه
        sent_msg = bot.send_message(
            ADMIN_ID,
            msg_for_admin,
            parse_mode='Markdown',
            reply_markup=reply_buttons(user.id, message.message_id)
        )
        
        # ذخیره در دیتابیس
        messages_db.append({
            'user_id': user.id,
            'user_name': user.first_name,
            'text': text,
            'time': time.time(),
            'user_msg_id': message.message_id,
            'admin_msg_id': sent_msg.message_id
        })
        
        # تأییدیه به کاربر
        bot.reply_to(message, "✅ پیام شما ارسال شد!")
        
        save_to_file()
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, "⚠️ خطا در ارسال، لطفاً مجدد تلاش کنید")

# ============ پیام از ادمین ============
@bot.message_handler(func=lambda m: str(m.from_user.id) == ADMIN_ID and not m.text.startswith('/'))
def handle_admin_message(message):
    """پردازش پاسخ ادمین"""
    if ADMIN_ID in active_replies:
        target_user_id = active_replies[ADMIN_ID]
        reply_text = message.text
        
        print(f"📤 پاسخ ادمین به کاربر {target_user_id}: {reply_text[:50]}...")
        
        try:
            # پیدا کردن نام کاربر
            user_name = "کاربر"
            for msg in messages_db:
                if str(msg['user_id']) == target_user_id:
                    user_name = msg['user_name']
                    break
            
            # ارسال پاسخ به کاربر
            response = f"""
            📨 *پاسخ از صاحب ربات:*
            
            {reply_text}
            
            🔄 برای پاسخ مجدد، پیام جدید بنویسید.
            """
            
            bot.send_message(target_user_id, response, parse_mode='Markdown')
            
            # تأیید به ادمین
            bot.reply_to(message, f"✅ پاسخ به {user_name} ارسال شد!")
            
            # حذف وضعیت پاسخ
            del active_replies[ADMIN_ID]
            
        except Exception as e:
            print(f"❌ خطا در ارسال پاسخ: {e}")
            bot.reply_to(message, "❌ کاربر ربات را بلاک کرده یا حذف شده است")
            del active_replies[ADMIN_ID]
    else:
        bot.reply_to(message, "💡 برای پاسخ، روی دکمه '📩 پاسخ' کلیک کنید")

# ============ مدیریت دکمه‌ها ============
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """مدیریت کلیک روی دکمه‌ها"""
    try:
        # فقط ادمین می‌تواند کلیک کند
        if str(call.from_user.id) != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ دسترسی ندارید")
            return
        
        # پاسخ به کاربر
        if call.data.startswith('reply_'):
            parts = call.data.split('_')
            if len(parts) >= 3:
                target_user_id = parts[1]
                target_msg_id = parts[2]
                
                # ذخیره وضعیت پاسخ
                active_replies[ADMIN_ID] = target_user_id
                
                # پیدا کردن نام کاربر
                user_name = "کاربر"
                for msg in messages_db:
                    if str(msg['user_id']) == target_user_id:
                        user_name = msg['user_name']
                        break
                
                # ویرایش پیام اصلی
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=call.message.text + "\n\n⏳ *در حال پاسخ...*",
                    parse_mode='Markdown'
                )
                
                # راهنمایی به ادمین
                guide = f"""
                ✍️ *در حال پاسخ به {user_name}*
                
                🆔 آیدی: `{target_user_id}`
                
                📝 لطفا پیام پاسخ را بنویسید و ارسال کنید.
                
                برای لغو: /cancel
                """
                
                bot.send_message(
                    ADMIN_ID,
                    guide,
                    parse_mode='Markdown',
                    reply_markup=cancel_button()
                )
                
                bot.answer_callback_query(call.id, "📝 پیام پاسخ را بنویسید")
        
        # مشاهده کاربر
        elif call.data.startswith('view_'):
            user_id = call.data.split('_')[1]
            
            # پیدا کردن پیام‌های کاربر
            user_messages = [m for m in messages_db if str(m['user_id']) == user_id]
            
            if user_messages:
                user_name = user_messages[0]['user_name']
                info = f"""
                👤 *مشاهده کاربر*
                
                نام: {user_name}
                آیدی: `{user_id}`
                تعداد پیام: {len(user_messages)}
                
                آخرین پیام:
                {user_messages[-1]['text'][:100]}...
                """
                bot.send_message(ADMIN_ID, info, parse_mode='Markdown')
            else:
                bot.answer_callback_query(call.id, "⚠️ کاربر یافت نشد")
        
        # لغو پاسخ
        elif call.data == 'cancel_reply':
            if ADMIN_ID in active_replies:
                del active_replies[ADMIN_ID]
            
            bot.delete_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
            
            bot.answer_callback_query(call.id, "✅ پاسخ لغو شد")
        
        save_to_file()
        
    except Exception as e:
        print(f"❌ خطا در callback: {e}")
        bot.answer_callback_query(call.id, "❌ خطایی رخ داد")

# ============ رسانه از کاربران ============
@bot.message_handler(content_types=['photo', 'video', 'document', 'voice'])
def handle_media(message):
    """پردازش رسانه از کاربران"""
    if str(message.from_user.id) == ADMIN_ID:
        return
    
    user = message.from_user
    
    try:
        # فوروارد به ادمین
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        
        # اطلاع‌رسانی
        media_type = {
            'photo': 'عکس',
            'video': 'ویدیو',
            'document': 'فایل',
            'voice': 'پیام صوتی'
        }.get(message.content_type, 'رسانه')
        
        notify = f"""
        📎 {media_type} جدید
        
        👤 از: {user.first_name}
        🆔 آیدی: `{user.id}`
        """
        
        bot.send_message(
            ADMIN_ID,
            notify,
            parse_mode='Markdown',
            reply_markup=reply_buttons(user.id, message.message_id)
        )
        
        # تأییدیه به کاربر
        bot.reply_to(message, f"✅ {media_type} شما ارسال شد!")
        
    except Exception as e:
        print(f"❌ خطا در ارسال رسانه: {e}")

# ============ اجرای ربات ============
print("🔄 اتصال به تلگرام...")

def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=30)
        except Exception as e:
            print(f"⚠️ خطا در اتصال: {e}")
            print("⏳ 10 ثانیه تا تلاش مجدد...")
            time.sleep(10)
            save_to_file()

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n👋 ربات متوقف شد")
        save_to_file()
