# -*- coding: utf-8 -*-
import telebot
import time
import json
import os
from telebot import types

# تنظیمات ربات
TOKEN = "8511185751:AAHpc-PTFtCNyBGrSknSKHv_6iV2O3Rdy4U"
YOUR_CHAT_ID = "1761692934"

# ایجاد ربات
bot = telebot.TeleBot(TOKEN)

# ساختارهای داده
recent_messages = []  # پیام‌های اخیر
MAX_MESSAGES = 50  # حداکثر تعداد پیام ذخیره شده

# دیکشنری برای ذخیره وضعیت ریپلای کاربران
reply_sessions = {}  # {admin_id: {'target_user_id': X, 'target_message_id': Y, 'reply_text': ''}}

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
    except:
        pass

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
    except:
        print("⚠️ خطا در بارگذاری داده‌ها")

# بارگذاری داده‌های قبلی
load_data()

# === دکمه‌های ریپلای ===
def create_reply_keyboard(user_id, message_id):
    """ایجاد کیبورد ریپلای برای ادمین"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    btn_reply = types.InlineKeyboardButton(
        text="📩 ریپلای به کاربر", 
        callback_data=f"reply_{user_id}_{message_id}"
    )
    
    btn_cancel = types.InlineKeyboardButton(
        text="❌ لغو ریپلای", 
        callback_data=f"cancel_reply"
    )
    
    keyboard.add(btn_reply, btn_cancel)
    return keyboard

def create_cancel_keyboard():
    """دکمه لغو هنگام ریپلای"""
    keyboard = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(
        text="❌ انصراف از ارسال", 
        callback_data="cancel_send"
    )
    keyboard.add(btn)
    return keyboard

# === هندلر اصلی برای کاربران عادی ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = """
    👋 *سلام!*
    
    این ربات پیام‌رسان است. هر پیامی که بفرستید:
    1️⃣ برای صاحب ربات ارسال می‌شود
    2️⃣ تأییدیه دریافت به شما نمایش داده می‌شود
    
    ✍️ *کافیه پیام خود را بنویسید*
    
    ⚠️ *نکته:* پیام‌ها به صورت ناشناس ارسال می‌شوند
    """
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')
    
    # اطلاع به شما از کاربر جدید
    try:
        user_info = f"""
        👤 *کاربر جدید:*
        نام: {message.from_user.first_name}
        یوزرنیم: @{message.from_user.username if message.from_user.username else 'ندارد'}
        آیدی: `{message.from_user.id}`
        """
        msg = bot.send_message(YOUR_CHAT_ID, user_info, parse_mode='Markdown')
        
        # اضافه کردن دکمه ریپلای
        bot.edit_message_reply_markup(
            chat_id=YOUR_CHAT_ID,
            message_id=msg.message_id,
            reply_markup=create_reply_keyboard(message.from_user.id, msg.message_id)
        )
        
    except Exception as e:
        print(f"⚠️ خطا در اطلاع‌رسانی: {e}")

# === هندلر برای پیام‌های کاربران (غیر ادمین) ===
@bot.message_handler(func=lambda message: str(message.from_user.id) != YOUR_CHAT_ID)
def forward_user_message(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "بدون یوزرنیم"
    user_text = message.text
    
    # جلوگیری از فوروارد کردن دستورات
    if user_text.startswith('/'):
        return
    
    print(f"📩 پیام جدید از {user_name}: {user_text[:50]}...")
    
    try:
        # 1. فوروارد پیام به شما (با اطلاعات کاربر)
        forward_info = f"""
        📬 *پیام جدید از کاربر:*
        
        👤 نام: {user_name}
        🆔 آیدی: `{user_id}`
        📝 یوزرنیم: {username}
        
        ✉️ *پیام:*
        {user_text}
        
        ⏰ زمان: {time.strftime('%H:%M:%S')}
        """
        
        # ارسال پیام به ادمین
        msg_to_admin = bot.send_message(
            YOUR_CHAT_ID, 
            forward_info,
            parse_mode='Markdown',
            reply_markup=create_reply_keyboard(user_id, message.message_id)
        )
        
        # 2. ذخیره پیام در لیست
        recent_messages.append({
            'user_id': user_id,
            'user_name': user_name,
            'text': user_text,
            'time': time.time(),
            'user_message_id': message.message_id,
            'admin_message_id': msg_to_admin.message_id
        })
        
        # محدود کردن حجم لیست
        if len(recent_messages) > MAX_MESSAGES:
            recent_messages.pop(0)
        
        # 3. تأییدیه به کاربر
        confirmation = f"""
        ✅ *پیام شما ارسال شد!*
        
        متن شما:
        "{user_text[:100]}{'...' if len(user_text) > 100 else ''}"
        
        🔄 برای ارسال پیام جدید، کافیست بنویسید.
        """
        
        bot.reply_to(message, confirmation, parse_mode='Markdown')
        
        # ذخیره داده‌ها
        save_data()
        
    except Exception as e:
        print(f"❌ خطا در ارسال پیام: {e}")
        bot.reply_to(message, "❌ متأسفانه خطایی در ارسال پیام رخ داد. لطفاً مجدد تلاش کنید.")

# === هندلر برای callback دکمه‌ها ===
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """مدیریت کلیک روی دکمه‌های اینلاین"""
    try:
        admin_id = str(call.from_user.id)
        
        # بررسی دسترسی ادمین
        if admin_id != YOUR_CHAT_ID:
            bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
            return
        
        # ریپلای به کاربر
        if call.data.startswith('reply_'):
            parts = call.data.split('_')
            if len(parts) >= 3:
                target_user_id = parts[1]
                target_message_id = parts[2] if len(parts) > 2 else None
                
                # ذخیره وضعیت ریپلای
                reply_sessions[admin_id] = {
                    'target_user_id': target_user_id,
                    'target_message_id': target_message_id,
                    'status': 'waiting_for_reply'
                }
                
                # پیدا کردن نام کاربر
                user_name = "کاربر"
                for msg in recent_messages:
                    if str(msg['user_id']) == target_user_id:
                        user_name = msg['user_name']
                        break
                
                # پیام راهنمایی به ادمین
                guide_text = f"""
                ✍️ *در حال پاسخ به {user_name}...*
                
                🆔 آیدی کاربر: `{target_user_id}`
                
                📝 لطفا پیام پاسخ خود را بنویسید.
                
                ⚠️ پیام شما مستقیماً برای کاربر ارسال می‌شود.
                
                برای انصراف دکمه ❌ زیر را بزنید.
                """
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=call.message.text + "\n\n" + "⏳ در حال انتظار برای پاسخ شما...",
                    parse_mode='Markdown'
                )
                
                # ارسال پیام جداگانه با دکمه لغو
                cancel_msg = bot.send_message(
                    YOUR_CHAT_ID,
                    guide_text,
                    parse_mode='Markdown',
                    reply_markup=create_cancel_keyboard()
                )
                
                # ذخیره ID پیام لغو
                reply_sessions[admin_id]['cancel_message_id'] = cancel_msg.message_id
                
                bot.answer_callback_query(call.id, "📝 لطفا پاسخ خود را بنویسید")
        
        # لغو ریپلای
        elif call.data == 'cancel_reply':
            if admin_id in reply_sessions:
                del reply_sessions[admin_id]
            
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
            
            bot.answer_callback_query(call.id, "✅ ریپلای لغو شد")
        
        # لغو ارسال
        elif call.data == 'cancel_send':
            if admin_id in reply_sessions:
                # حذف پیام راهنمایی
                try:
                    bot.delete_message(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id
                    )
                except:
                    pass
                
                # حذف وضعیت ریپلای
                del reply_sessions[admin_id]
                
                bot.answer_callback_query(call.id, "✅ ارسال پیام لغو شد")
            else:
                bot.answer_callback_query(call.id, "⚠️ وضعیت ریپلای یافت نشد")
        
        save_data()
        
    except Exception as e:
        print(f"❌ خطا در callback: {e}")
        bot.answer_callback_query(call.id, "❌ خطایی رخ داد")

# === هندلر جداگانه برای پیام‌های ادمین ===
@bot.message_handler(func=lambda message: str(message.from_user.id) == YOUR_CHAT_ID)
def handle_admin_message(message):
    """مدیریت پیام‌های ادمین"""
    admin_id = str(message.from_user.id)
    
    # اگر ادمین در حالت ریپلای است
    if admin_id in reply_sessions and reply_sessions[admin_id].get('status') == 'waiting_for_reply':
        handle_admin_reply(message)
    else:
        # اگر دستور ادمین است
        handle_admin_command(message)

def handle_admin_reply(message):
    """پردازش پاسخ ادمین به کاربر"""
    try:
        admin_id = str(message.from_user.id)
        session = reply_sessions[admin_id]
        target_user_id = session['target_user_id']
        reply_text = message.text
        
        # جلوگیری از پردازش دستورات به عنوان ریپلای
        if reply_text.startswith('/'):
            handle_admin_command(message)
            return
        
        print(f"📤 ادمین در حال پاسخ به کاربر {target_user_id}: {reply_text[:50]}...")
        
        # ارسال پاسخ به کاربر
        try:
            # پیدا کردن نام کاربر
            user_name = "کاربر"
            for msg in recent_messages:
                if str(msg['user_id']) == target_user_id:
                    user_name = msg['user_name']
                    break
            
            # پیام به کاربر
            user_response = f"""
            📨 *پاسخ از صاحب ربات:*
            
            {reply_text}
            
            🔄 برای پاسخ مجدد، پیام جدید بنویسید.
            """
            
            bot.send_message(
                target_user_id,
                user_response,
                parse_mode='Markdown'
            )
            
            # تأیید به ادمین
            success_msg = f"""
            ✅ *پاسخ شما ارسال شد!*
            
            به: {user_name}
            آیدی: `{target_user_id}`
            
            📝 متن پاسخ:
            {reply_text}
            """
            
            bot.reply_to(message, success_msg, parse_mode='Markdown')
            
            # حذف پیام راهنمایی لغو
            if 'cancel_message_id' in session:
                try:
                    bot.delete_message(
                        chat_id=message.chat.id,
                        message_id=session['cancel_message_id']
                    )
                except:
                    pass
            
            # حذف وضعیت ریپلای
            del reply_sessions[admin_id]
            
            # علامت‌گذاری پیام اصلی
            for msg in recent_messages:
                if str(msg['user_id']) == target_user_id:
                    try:
                        # بروزرسانی متن پیام اصلی
                        updated_text = bot.edit_message_text(
                            chat_id=YOUR_CHAT_ID,
                            message_id=msg.get('admin_message_id'),
                            text=f"✅ *پاسخ داده شده*\n\n{message.text}",
                            parse_mode='Markdown',
                            reply_markup=None
                        )
                    except Exception as e:
                        print(f"⚠️ خطا در بروزرسانی پیام: {e}")
                    break
            
        except Exception as e:
            print(f"❌ خطا در ارسال پاسخ به کاربر: {e}")
            
            # اطلاع به ادمین
            error_msg = f"""
            ❌ *خطا در ارسال پاسخ!*
            
            دلیل: کاربر ربات را مسدود کرده یا حذف کرده است.
            
            آیدی کاربر: `{target_user_id}`
            """
            
            bot.reply_to(message, error_msg, parse_mode='Markdown')
            
            # حذف وضعیت ریپلای
            if admin_id in reply_sessions:
                del reply_sessions[admin_id]
        
        save_data()
        
    except Exception as e:
        print(f"❌ خطا در handle_admin_reply: {e}")

def handle_admin_command(message):
    """پردازش دستورات ادمین"""
    admin_id = str(message.from_user.id)
    text = message.text
    
    # دستور /admin
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
    
    # دستور /stats
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
    
    # دستور /recent
    elif text == '/recent':
        if not recent_messages:
            bot.reply_to(message, "📭 هیچ پیامی ذخیره نشده است")
            return
        
        recent_text = "📨 *آخرین 10 پیام:*\n\n"
        for i, msg in enumerate(recent_messages[-10:], 1):
            recent_text += f"{i}. {msg['user_name']} (آیدی: `{msg['user_id']}`): {msg['text'][:40]}...\n"
        
        bot.reply_to(message, recent_text, parse_mode='Markdown')
    
    # دستور /clear
    elif text == '/clear':
        recent_messages.clear()
        save_data()
        bot.reply_to(message, "✅ همه پیام‌های ذخیره شده پاک شدند")
    
    # دستور /cancel
    elif text == '/cancel':
        if admin_id in reply_sessions:
            del reply_sessions[admin_id]
            save_data()
            bot.reply_to(message, "✅ ریپلای فعلی لغو شد")
        else:
            bot.reply_to(message, "⚠️ وضعیت ریپلای فعالی وجود ندارد")
    
    else:
        # اگر پیام عادی ادمین است و در حالت ریپلای نیست
        bot.reply_to(message, "💡 برای پاسخ به کاربران، روی دکمه 'ریپلای به کاربر' کلیک کنید.")

# === رسانه از کاربران ===
@bot.message_handler(content_types=['photo', 'video', 'document', 'voice'])
def forward_media(message):
    # فقط از کاربران غیر ادمین
    if str(message.from_user.id) == YOUR_CHAT_ID:
        return
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    try:
        # فوروارد رسانه به شما
        bot.forward_message(YOUR_CHAT_ID, message.chat.id, message.message_id)
        
        # اطلاع رسانی به شما
        media_type = {
            'photo': 'عکس',
            'video': 'ویدیو',
            'document': 'فایل',
            'voice': 'ویس'
        }.get(message.content_type, 'رسانه')
        
        info = f"📎 {media_type} جدید از {user_name} (آیدی: {user_id})"
        
        # ارسال اطلاع با دکمه ریپلای
        msg = bot.send_message(
            YOUR_CHAT_ID, 
            info,
            reply_markup=create_reply_keyboard(user_id, message.message_id)
        )
        
        # ذخیره در لیست
        recent_messages.append({
            'user_id': user_id,
            'user_name': user_name,
            'text': f"[{media_type}]",
            'time': time.time(),
            'user_message_id': message.message_id,
            'admin_message_id': msg.message_id
        })
        
        # تأییدیه به کاربر
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
            save_data()  # ذخیره داده‌ها قبل از تلاش مجدد

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n👋 ربات متوقف شد. ذخیره داده‌ها...")
        save_data()
