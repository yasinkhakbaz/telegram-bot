# -*- coding: utf-8 -*-
import telebot
import time
import json
import os
from datetime import datetime, timezone, timedelta
from telebot import types

# تنظیمات ربات
TOKEN = "8313399802:AAEb3dsc9PfYn3LFreycmxo9I2ycwL3PXuY"
YOUR_CHAT_ID = "1761692934"

# ایجاد ربات
bot = telebot.TeleBot(TOKEN)

# تنظیم منطقه زمانی ایران (GMT+3:30)
IRAN_TZ = timezone(timedelta(hours=3, minutes=30))

# ساختارهای داده
recent_messages = []  # پیام‌های اخیر
MAX_MESSAGES = 100  # حداکثر تعداد پیام ذخیره شده
blocked_users = []  # لیست کاربران بلاک شده
users_data = {}  # اطلاعات کاربران

# دیکشنری برای ذخیره وضعیت ریپلای کاربران
reply_sessions = {}  # {admin_id: {'target_user_id': X, 'target_message_id': Y}}

# فایل ذخیره داده‌ها
DATA_FILE = "bot_data.json"
BLOCKED_FILE = "blocked_users.json"
USERS_FILE = "users_data.json"

print("🤖 ربات پیام‌رسان پیشرفته فعال شد!")
print(f"🆔 آیدی ادمین: {YOUR_CHAT_ID}")
print("⏰ منطقه زمانی: ایران (GMT+3:30)")
print("📱 منتظر پیام کاربران...")

# === توابع کمکی ===
def get_iran_time():
    """دریافت زمان فعلی ایران"""
    return datetime.now(IRAN_TZ)

def format_time(timestamp):
    """فرمت‌دهی زمان به شکل فارسی"""
    dt = datetime.fromtimestamp(timestamp, IRAN_TZ)
    return dt.strftime("%Y/%m/%d %H:%M")

def save_all_data():
    """ذخیره همه داده‌ها در فایل"""
    try:
        # ذخیره پیام‌ها
        messages_data = {
            'recent_messages': recent_messages[-MAX_MESSAGES:],
            'reply_sessions': reply_sessions
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages_data, f, ensure_ascii=False, indent=2)
        
        # ذخیره کاربران بلاک شده
        with open(BLOCKED_FILE, 'w', encoding='utf-8') as f:
            json.dump(blocked_users, f, ensure_ascii=False, indent=2)
        
        # ذخیره اطلاعات کاربران
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
            
        print(f"💾 داده‌ها ذخیره شد: {len(recent_messages)} پیام, {len(blocked_users)} بلاک شده")
    except Exception as e:
        print(f"⚠️ خطا در ذخیره داده‌ها: {e}")

def load_all_data():
    """بارگذاری همه داده‌ها از فایل"""
    global recent_messages, blocked_users, users_data, reply_sessions
    
    try:
        # بارگذاری پیام‌ها
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                recent_messages = data.get('recent_messages', [])
                reply_sessions = data.get('reply_sessions', {})
                print(f"📂 پیام‌ها بارگذاری شد: {len(recent_messages)}")
        
        # بارگذاری کاربران بلاک شده
        if os.path.exists(BLOCKED_FILE):
            with open(BLOCKED_FILE, 'r', encoding='utf-8') as f:
                blocked_users = json.load(f)
                print(f"🚫 کاربران بلاک شده: {len(blocked_users)}")
        
        # بارگذاری اطلاعات کاربران
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
                print(f"👥 اطلاعات کاربران: {len(users_data)} کاربر")
                
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری داده‌ها: {e}")

# بارگذاری داده‌های قبلی
load_all_data()

def update_user_data(user_id, user_name, username=""):
    """به‌روزرسانی اطلاعات کاربر"""
    user_id_str = str(user_id)
    
    if user_id_str not in users_data:
        users_data[user_id_str] = {
            'name': user_name,
            'username': username,
            'first_seen': time.time(),
            'last_seen': time.time(),
            'message_count': 1,
            'is_blocked': user_id in blocked_users
        }
    else:
        users_data[user_id_str]['last_seen'] = time.time()

        users_data[user_id_str]['message_count'] += 1
        if users_data[user_id_str]['name'] != user_name:
            users_data[user_id_str]['name'] = user_name
        if username and users_data[user_id_str]['username'] != username:
            users_data[user_id_str]['username'] = username

# === دکمه‌های پیشرفته ===
def create_advanced_keyboard(user_id, message_id):
    """ایجاد کیبورد پیشرفته برای ادمین"""
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    
    btn_reply = types.InlineKeyboardButton("📩 پاسخ", callback_data=f"reply_{user_id}_{message_id}")
    
    # بررسی وضعیت بلاک/آنبلاک
    is_blocked = user_id in blocked_users
    if is_blocked:
        btn_block = types.InlineKeyboardButton("✅ آنبلاک", callback_data=f"unblock_{user_id}")
    else:
        btn_block = types.InlineKeyboardButton("🚫 بلاک", callback_data=f"block_{user_id}")
    
    btn_profile = types.InlineKeyboardButton("👤 پروفایل", callback_data=f"profile_{user_id}")
    btn_messages = types.InlineKeyboardButton("📨 پیام‌ها", callback_data=f"messages_{user_id}")
    btn_delete = types.InlineKeyboardButton("🗑️ حذف", callback_data=f"delete_{message_id}")
    btn_cancel = types.InlineKeyboardButton("❌ لغو ریپلای", callback_data=f"cancel_reply_{user_id}")
    
    keyboard.add(btn_reply, btn_block, btn_profile)
    keyboard.add(btn_messages, btn_delete, btn_cancel)
    
    return keyboard

def create_reply_keyboard():
    """کیبورد برای حالت پاسخ"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    btn_cancel = types.InlineKeyboardButton("❌ لغو ریپلای", callback_data="cancel_send")
    btn_block = types.InlineKeyboardButton("🚫 بلاک کاربر", callback_data="reply_block")
    btn_unblock = types.InlineKeyboardButton("✅ آنبلاک کاربر", callback_data="reply_unblock")
    
    keyboard.add(btn_cancel, btn_block, btn_unblock)
    
    return keyboard

def create_admin_panel_keyboard():
    """کیبورد پنل ادمین"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    btn_stats = types.InlineKeyboardButton("📊 آمار", callback_data="admin_stats")
    btn_users = types.InlineKeyboardButton("👥 کاربران", callback_data="admin_users")
    btn_messages = types.InlineKeyboardButton("📨 پیام‌ها", callback_data="admin_messages")
    btn_blocked = types.InlineKeyboardButton("🚫 بلاک شده‌ها", callback_data="admin_blocked")
    btn_backup = types.InlineKeyboardButton("💾 پشتیبان", callback_data="admin_backup")
    btn_clean = types.InlineKeyboardButton("🧹 پاکسازی", callback_data="admin_clean")
    
    keyboard.add(btn_stats, btn_users, btn_messages, btn_blocked, btn_backup, btn_clean)
    
    return keyboard

# === دستورات کاربران ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user = message.from_user
    user_id = user.id
    
    # چک کردن بلاک بودن
    if user_id in blocked_users:
        bot.send_message(message.chat.id, "🚫 شما توسط ادمین بلاک شده‌اید.")
        return
    
    # به‌روزرسانی اطلاعات کاربر
    update_user_data(user_id, user.first_name, user.username)
    
    welcome_text = f"""
    سلام {user.first_name}! 👋

    🤖 *ربات پیام‌رسان پیشرفته*

    ✍️ هر پیامی که بفرستی، مستقیم به صاحب ربات می‌رسه.
    ✅ تأییدیه هم دریافت می‌کنی.

    🔒 حریم خصوصی کامل

    🆔 آیدی شما: {user_id}
    """
    
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')
    
    # اطلاع به ادمین
    try:
        user_info = f"""
        👤 *کاربر جدید/بازگشته*
        
        نام: {user.first_name}
        یوزرنیم: @{user.username if user.username else 'ندارد'}
        آیدی: {user_id}
        
        📅 اولین بازدید: {format_time(users_data[str(user_id)]['first_seen'])}
        """
        
        msg = bot.send_message(
            YOUR_CHAT_ID, 
            user_info, 
            parse_mode='Markdown',
            reply_markup=create_advanced_keyboard(user_id, message.message_id)
        )
        
    except Exception as e:
        print(f"⚠️ خطا در اطلاع‌رسانی: {e}")

# === پیام از کاربران ===
@bot.message_handler(func=lambda m: str(m.from_user.id) != YOUR_CHAT_ID and not m.text.startswith('/'))
def handle_user_message(message):
    user = message.from_user
    user_id = user.id
    text = message.text
    
    # چک کردن بلاک بودن
    if user_id in blocked_users:
        bot.send_message(message.chat.id, "🚫 شما بلاک شده‌اید.")
        return
    
    print(f"📩 پیام از {user.first_name} ({user_id}): {text[:50]}...")
    
    try:
        # به‌روزرسانی اطلاعات کاربر
        update_user_data(user_id, user.first_name, user.username)
        
        # ساخت پیام برای ادمین
        msg_for_admin = f"""
        📬 *پیام جدید*
        
        👤: {user.first_name}
        🆔: {user_id}
        📅: {get_iran_time().strftime("%H:%M:%S")}
        
        ✉️:
        {text}
        
        📊 پیام شماره: {users_data[str(user_id)]['message_count']}
        """
        
        # ارسال به ادمین
        sent_msg = bot.send_message(
            YOUR_CHAT_ID,
            msg_for_admin,
            parse_mode='Markdown',
            reply_markup=create_advanced_keyboard(user_id, message.message_id)
        )
        
        # ذخیره پیام
        recent_messages.append({
            'user_id': user_id,
            'user_name': user.first_name,
            'text': text,
            'time': time.time(),
            'user_msg_id': message.message_id,
            'admin_msg_id': sent_msg.message_id
        })
        
        # تأییدیه به کاربر
        bot.reply_to(message, "✅ پیام شما ارسال شد!")
        
        save_all_data()
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        bot.reply_to(message, "⚠️ خطا در ارسال")

# === مدیریت ادمین ===
@bot.message_handler(commands=['admin', 'panel'])
def admin_panel(message):
    if str(message.from_user.id) != YOUR_CHAT_ID:
        bot.reply_to(message, "❌ دسترسی ندارید!")
        return
    
    panel_text = f"""
    🛠️ *پنل مدیریت پیشرفته*
    
    📊 آمار کلی:
    • کاربران: {len(users_data)}
    • پیام‌ها: {len(recent_messages)}
    • بلاک شده: {len(blocked_users)}
    
    ⚡ دستورات سریع:
    /stats - آمار دقیق
    /users - لیست کاربران
    /search [آیدی] - جستجوی کاربر
    /block [آیدی] - بلاک کاربر
    /unblock [آیدی] - آنبلاک کاربر
    /broadcast [متن] - ارسال به همه
    /cancel - لغو پاسخ فعلی
    """
    
    bot.send_message(
        message.chat.id,
        panel_text,
        parse_mode='Markdown',
        reply_markup=create_admin_panel_keyboard()
    )

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if str(message.from_user.id) != YOUR_CHAT_ID:
        return
    
    # محاسبه آمار
    total_messages = len(recent_messages)
    unique_users = len(users_data)
    
    # پیام‌های امروز
    today = time.time() - 86400
    today_messages = len([m for m in recent_messages if m['time'] > today])
    
    # کاربران فعال امروز
    active_today = len([uid for uid, data in users_data.items() 
                       if data['last_seen'] > today])
    
    # زمان ایرانی
    iran_time = get_iran_time()
    
    stats_text = f"""
    📈 *آمار دقیق ربات*
    
    👥 کاربران:
    • کل کاربران: {unique_users}
    • فعال امروز: {active_today}
    • بلاک شده: {len(blocked_users)}
    
    📨 پیام‌ها:
    • کل پیام‌ها: {total_messages}
    • پیام‌های امروز: {today_messages}
    • میانگین پیام/کاربر: {round(total_messages/unique_users, 2) if unique_users > 0 else 0}
    
    ⏰ زمان (ایران):
    • زمان فعلی: {iran_time.strftime('%Y/%m/%d %H:%M:%S')}
    • اولین کاربر: {format_time(min([data['first_seen'] for data in users_data.values()])) if users_data else 'ندارد'}
    • آخرین فعالیت: {format_time(max([data['last_seen'] for data in users_data.values()])) if users_data else 'ندارد'}
    """
    
    bot.reply_to(message, stats_text, parse_mode='Markdown')

@bot.message_handler(commands=['users'])
def list_users(message):
    if str(message.from_user.id) != YOUR_CHAT_ID:
        return
    
    if not users_data:
        bot.reply_to(message, "📭 هیچ کاربری ثبت نشده است")
        return
    
    users_list = "👥 *لیست کاربران:*\n\n"
    
    # مرتب‌سازی براساس آخرین فعالیت
    sorted_users = sorted(users_data.items(), 
                         key=lambda x: x[1]['last_seen'], 
                         reverse=True)[:20]  # 20 کاربر آخر
    
    for i, (user_id, data) in enumerate(sorted_users, 1):
        status = "🚫" if int(user_id) in blocked_users else "✅"
        last_seen = format_time(data['last_seen'])
        users_list += f"{i}. {status} {data['name']} (آیدی: {user_id})\n"
        users_list += f"   📨 {data['message_count']} پیام | 📅 {last_seen}\n\n"
    
    bot.reply_to(message, users_list, parse_mode='Markdown')

@bot.message_handler(commands=['search'])
def search_user(message):
    if str(message.from_user.id) != YOUR_CHAT_ID:
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ استفاده: /search [آیدی یا نام]")
        return
    
    search_term = parts[1]
    results = []
    
    for user_id, data in users_data.items():
        if (search_term in str(user_id) or 
            search_term.lower() in data['name'].lower() or
            (data['username'] and search_term.lower() in data['username'].lower())):
            results.append((user_id, data))
    
    if not results:
        bot.reply_to(message, "🔍 کاربری یافت نشد")
        return
    
    search_text = f"🔍 *نتایج جستجو برای '{search_term}':*\n\n"
    
    for user_id, data in results[:10]:  # حداکثر 10 نتیجه
        status = "🚫 بلاک شده" if int(user_id) in blocked_users else "✅ فعال"
        last_seen = format_time(data['last_seen'])
        search_text += f"""
👤 *{data['name']}*
🆔 آیدی: {user_id}
📝 یوزرنیم: @{data['username'] or 'ندارد'}
📨 پیام‌ها: {data['message_count']}
📅 آخرین فعالیت: {last_seen}
🔰 وضعیت: {status}

"""
    
    bot.reply_to(message, search_text, parse_mode='Markdown')

@bot.message_handler(commands=['block'])
def block_user_cmd(message):
    if str(message.from_user.id) != YOUR_CHAT_ID:
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ استفاده: /block [آیدی کاربر]")
        return
    
    try:
        user_id = int(parts[1])
        
        if user_id in blocked_users:
            bot.reply_to(message, f"⚠️ کاربر {user_id} قبلاً بلاک شده است")
            return
        
        blocked_users.append(user_id)
        
        # آپدیت وضعیت در users_data
        if str(user_id) in users_data:
            users_data[str(user_id)]['is_blocked'] = True
        
        save_all_data()
        
        # اطلاع به کاربر (اگر ممکن باشد)
        try:
            bot.send_message(user_id, "🚫 شما توسط ادمین بلاک شده‌اید.")
        except:
            pass
        
        bot.reply_to(message, f"✅ کاربر {user_id} بلاک شد")
        
    except ValueError:
        bot.reply_to(message, "⚠️ آیدی باید عددی باشد")

@bot.message_handler(commands=['unblock'])
def unblock_user_cmd(message):
    if str(message.from_user.id) != YOUR_CHAT_ID:
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ استفاده: /unblock [آیدی کاربر]")
        return
    
    try:
        user_id = int(parts[1])
        
        if user_id not in blocked_users:
            bot.reply_to(message, f"⚠️ کاربر {user_id} بلاک نیست")
            return
        
        blocked_users.remove(user_id)
        
        # آپدیت وضعیت در users_data
        if str(user_id) in users_data:
            users_data[str(user_id)]['is_blocked'] = False
            save_all_data()
        
        # اطلاع به کاربر
        try:
            bot.send_message(user_id, "✅ شما توسط ادمین آنبلاک شده‌اید.")
        except:
            pass
        
        bot.reply_to(message, f"✅ کاربر {user_id} آنبلاک شد")
        
    except ValueError:
        bot.reply_to(message, "⚠️ آیدی باید عددی باشد")

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if str(message.from_user.id) != YOUR_CHAT_ID:
        return
    
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ استفاده: /broadcast [متن پیام]")
        return
    
    broadcast_text = parts[1]
    sent_count = 0
    failed_count = 0
    
    bot.reply_to(message, f"📢 در حال ارسال به {len(users_data)} کاربر...")
    
    for user_id_str in users_data.keys():
        try:
            user_id = int(user_id_str)
            if user_id not in blocked_users:
                bot.send_message(user_id, f"📢 *پیام همگانی:*\n\n{broadcast_text}", parse_mode='Markdown')
                sent_count += 1
                time.sleep(0.05)  # جلوگیری از محدودیت تلگرام
        except:
            failed_count += 1
    
    bot.reply_to(message, f"""
✅ ارسال همگانی تکمیل شد:
• ✅ ارسال شده: {sent_count}
• ❌ ناموفق: {failed_count}
• 🚫 بلاک شده: {len(blocked_users)}
""")

@bot.message_handler(commands=['cancel'])
def cancel_reply_cmd(message):
    """لغو پاسخ فعلی"""
    if str(message.from_user.id) != YOUR_CHAT_ID:
        return
    
    admin_id = str(message.from_user.id)
    if admin_id in reply_sessions:
        del reply_sessions[admin_id]
        bot.reply_to(message, "✅ وضعیت ریپلای لغو شد.")
    else:
        bot.reply_to(message, "⚠️ در حال حاضر در حال پاسخ نیستید.")

# === پیام‌های عادی از ادمین ===
@bot.message_handler(func=lambda m: str(m.from_user.id) == YOUR_CHAT_ID and not m.text.startswith('/'))
def handle_admin_message(message):
    """مدیریت پیام‌های عادی ادمین (برای پاسخ به کاربران)"""
    admin_id = str(message.from_user.id)
    
    # اگر در حالت ریپلای هست
    if admin_id in reply_sessions:
        reply_info = reply_sessions[admin_id]
        target_user_id = reply_info['target_user_id']
        
        try:
            # ارسال پیام به کاربر
            bot.send_message(
                target_user_id,
                f"📩 *پاسخ از ادمین:*\n\n{message.text}",
                parse_mode='Markdown'
            )
            
            # اطلاع به ادمین
            bot.reply_to(message, f"✅ پاسخ به کاربر {target_user_id} ارسال شد.")
            
            # ذخیره پیام ارسالی
            recent_messages.append({
                'user_id': int(YOUR_CHAT_ID),
                'user_name': 'Admin',
                'text': message.text,
                'time': time.time(),
                'is_reply': True,
                'target_user_id': int(target_user_id)
            })
            
            # پاک کردن وضعیت ریپلای
            del reply_sessions[admin_id]
            
            save_all_data()
            
        except Exception as e:
            bot.reply_to(message, f"❌ خطا در ارسال پاسخ: {e}")
            if "blocked" in str(e).lower() or "bot was blocked" in str(e).lower():
                bot.reply_to(message, "⚠️ کاربر ربات را بلاک کرده یا وجود ندارد.")
    else:
        # اگر پیام عادی ادمین هست
        pass

# === سیستم callback پیشرفته ===
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        admin_id = str(call.from_user.id)
        
        if admin_id != YOUR_CHAT_ID:
            bot.answer_callback_query(call.id, "❌ دسترسی ندارید!")
            return
        
        # جلوگیری از اجرای همزمان
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
        
        # پاسخ به کاربر
        if call.data.startswith('reply_'):
            parts = call.data.split('_')
            if len(parts) >= 3:
                target_user_id = parts[1]
                target_msg_id = parts[2]
                
                # ذخیره وضعیت ریپلای
                reply_sessions[admin_id] = {
                    'target_user_id': target_user_id,
                    'target_msg_id': target_msg_id,
                    'time': time.time()
                }
                
                user_name = users_data.get(target_user_id, {}).get('name', 'کاربر')
                
                # آپدیت پیام اصلی
                original_text = call.message.text
                if "⏳" not in original_text:
                    bot.edit_message_text(
                    chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=original_text + "\n\n⏳ *در حال پاسخ...*",
                        parse_mode='Markdown',
                        reply_markup=call.message.reply_markup
                    )
                
                # ارسال راهنما
                guide = f"""
                ✍️ *پاسخ به {user_name}*
                
                🆔 آیدی: {target_user_id}
                ⏰ زمان: {get_iran_time().strftime("%H:%M")}
                
                📝 پیام پاسخ را بنویسید و ارسال کنید.
                
                🔧 *دکمه‌های سریع:*
                """
                
                bot.send_message(
                    YOUR_CHAT_ID,
                    guide,
                    parse_mode='Markdown',
                    reply_markup=create_reply_keyboard()
                )
                
                bot.answer_callback_query(call.id, "📝 پیام پاسخ را بنویسید")
        
        # بلاک کاربر از ریپلای
        elif call.data == "reply_block":
            if admin_id in reply_sessions:
                target_user_id = reply_sessions[admin_id]['target_user_id']
                user_id = int(target_user_id)
                
                if user_id not in blocked_users:
                    blocked_users.append(user_id)
                    if str(user_id) in users_data:
                        users_data[str(user_id)]['is_blocked'] = True
                    
                    save_all_data()
                    
                    try:
                        bot.send_message(user_id, "🚫 شما توسط ادمین بلاک شده‌اید.")
                    except:
                        pass
                    
                    bot.answer_callback_query(call.id, f"✅ کاربر بلاک شد")
                    
                    # آپدیت پیام راهنما
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=call.message.text + "\n\n🚫 *کاربر بلاک شد*",
                        parse_mode='Markdown'
                    )
                else:
                    bot.answer_callback_query(call.id, "⚠️ کاربر قبلاً بلاک است")
        
        # آنبلاک کاربر از ریپلای
        elif call.data == "reply_unblock":
            if admin_id in reply_sessions:
                target_user_id = reply_sessions[admin_id]['target_user_id']
                user_id = int(target_user_id)
                
                if user_id in blocked_users:
                    blocked_users.remove(user_id)
                    if str(user_id) in users_data:
                        users_data[str(user_id)]['is_blocked'] = False
                    
                    save_all_data()
                    
                    try:
                        bot.send_message(user_id, "✅ شما توسط ادمین آنبلاک شده‌اید.")
                    except:
                        pass
                    
                    bot.answer_callback_query(call.id, f"✅ کاربر آنبلاک شد")
                    
                    # آپدیت پیام راهنما
                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=call.message.text + "\n\n✅ *کاربر آنبلاک شد*",
                        parse_mode='Markdown'
                    )
                else:
                    bot.answer_callback_query(call.id, "⚠️ کاربر بلاک نیست")
        
        # بلاک کاربر
        elif call.data.startswith('block_'):
            user_id = int(call.data.split('_')[1])
            
            if user_id not in blocked_users:
                blocked_users.append(user_id)

if str(user_id) in users_data:
                    users_data[str(user_id)]['is_blocked'] = True
                
                save_all_data()
                
                try:
                    bot.send_message(user_id, "🚫 شما توسط ادمین بلاک شده‌اید.")
                except:
                    pass
                
                bot.answer_callback_query(call.id, f"✅ کاربر {user_id} بلاک شد")
                
                # آپدیت کیبورد
                try:
                    bot.edit_message_reply_markup(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=create_advanced_keyboard(user_id, call.message.message_id)
                    )
                except:
                    pass
            else:
                bot.answer_callback_query(call.id, "⚠️ کاربر قبلاً بلاک است")
        
        # آنبلاک کاربر
        elif call.data.startswith('unblock_'):
            user_id = int(call.data.split('_')[1])
            
            if user_id in blocked_users:
                blocked_users.remove(user_id)
                if str(user_id) in users_data:
                    users_data[str(user_id)]['is_blocked'] = False
                
                save_all_data()
                
                try:
                    bot.send_message(user_id, "✅ شما توسط ادمین آنبلاک شده‌اید.")
                except:
                    pass
                
                bot.answer_callback_query(call.id, f"✅ کاربر {user_id} آنبلاک شد")
                
                # آپدیت کیبورد
                try:
                    bot.edit_message_reply_markup(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=create_advanced_keyboard(user_id, call.message.message_id)
                    )
                except:
                    pass
            else:
                bot.answer_callback_query(call.id, "⚠️ کاربر بلاک نیست")
        
        # لغو ریپلای
        elif call.data == "cancel_send" or call.data.startswith("cancel_reply"):
            if admin_id in reply_sessions:
                del reply_sessions[admin_id]
                bot.answer_callback_query(call.id, "✅ ریپلای لغو شد")
                
                # حذف پیام راهنما
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except:
                    pass
                
                bot.send_message(YOUR_CHAT_ID, "✅ وضعیت ریپلای لغو شد.")
            else:
                bot.answer_callback_query(call.id, "⚠️ ریپلای فعالی وجود ندارد")
        
        # پروفایل کاربر
        elif call.data.startswith('profile_'):
            user_id = call.data.split('_')[1]
            
            if user_id in users_data:
                data = users_data[user_id]
                user_id_int = int(user_id)
                
                profile_text = f"""
                👤 *پروفایل کاربر*
                
                📛 نام: {data['name']}
                🆔 آیدی: {user_id}
                📝 یوزرنیم: @{data['username'] or 'ندارد'}
                
                📊 آمار:
                • 📨 پیام‌ها: {data['message_count']}
                • 📅 اولین بازدید: {format_time(data['first_seen'])}
                • 📅 آخرین فعالیت: {format_time(data['last_seen'])}
                
                🔰 وضعیت: {"🚫 بلاک شده" if user_id_int in blocked_users else "✅ فعال"}
                
                ⏰ زمان محلی: {get_iran_time().strftime("%H:%M:%S")}
                """
                
                bot.send_message(
                    YOUR_CHAT_ID,
                    profile_text,

parse_mode='Markdown',
                    reply_markup=create_advanced_keyboard(user_id_int, call.message.message_id)
                )
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ کاربر یافت نشد")
        
        # پیام‌های کاربر
        elif call.data.startswith('messages_'):
            user_id = call.data.split('_')[1]
            user_messages = [m for m in recent_messages if m['user_id'] == int(user_id)]
            
            if not user_messages:
                bot.answer_callback_query(call.id, "📭 هیچ پیامی از این کاربر نیست")
                return
            
            messages_text = f"📨 *آخرین پیام‌های کاربر:*\n\n"
            
            for i, msg in enumerate(user_messages[-10:], 1):  # 10 پیام آخر
                msg_time = format_time(msg['time'])
                messages_text += f"{i}. 📅 {msg_time}\n"
                messages_text += f"   📝 {msg['text'][:100]}...\n\n"
            
            bot.send_message(YOUR_CHAT_ID, messages_text, parse_mode='Markdown')
            bot.answer_callback_query(call.id)
        
        # آمار ادمین
        elif call.data == "admin_stats":
            show_stats(call.message)
            bot.answer_callback_query(call.id)
        
        # لیست کاربران ادمین
        elif call.data == "admin_users":
            list_users(call.message)
            bot.answer_callback_query(call.id)
            
    except Exception as e:
        print(f"❌ خطا در callback: {e}")
        try:
            bot.answer_callback_query(call.id, f"⚠️ خطا: {str(e)[:50]}")
        except:
            pass

# === اجرای ربات ===
if name == "main":
    print("🔄 ربات در حال اجرا...")
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"❌ خطا در اجرای ربات: {e}")
        time.sleep(5)
        print("🔄 تلاش مجدد برای اجرا...")    
