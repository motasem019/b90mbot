import threading
import json
import random
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

TOKEN = os.environ['TOKEN']        # ✅ هذا الصح
OWNER_ID = 6477948691
DATA_FILE = 'confessions.json'

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"messages": [], "users": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = []
    if user.id == OWNER_ID:
        keyboard.append([InlineKeyboardButton("📢 إرسال إذاعة", callback_data="broadcast_mode")])
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        """✨ *أهلاً وسهلاً!*

مرحبًا بك في *بوت الصراحة المجهول* 💬  
هنا تقدر ترسل رأيك، فضفضتك، أو سؤالك *بكل خصوصية* — بدون ما أحد يعرفك أبدًا 🙊

🔐 المالك وحده هو اللي يستلم الرسائل  
👑 حساب المالك: @Evil\\_1\\_0

👇 أرسل رسالتك الآن، واحنا بانتظارك 💌""",
        parse_mode="Markdown",
        reply_markup=markup
    )

async def receive_confession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    data = load_data()

    if user_id == OWNER_ID:
        return await update.message.reply_text("🚫 هذا البوت مخصص لاستقبال الصراحات فقط.")
    if user_id not in data["users"]:
        data["users"].append(user_id)

    msg_id = len(data["messages"]) + 1
    sent = await context.bot.send_message(
        OWNER_ID,
        f"📨 صراحة جديدة #{msg_id}:\n\n💬 {text}\n\n↩️ للرد: اضغط رد على هذه الرسالة"
    )
    data["messages"].append({
        "id": msg_id,
        "user_id": user_id,
        "message": text,
        "tg_message_id": sent.message_id,
        "timestamp": datetime.now().isoformat(),
        "reply": None
    })
    save_data(data)
    await update.message.reply_text("📩 تم استلام صراحتك بسرّية، شكرًا لثقتك!")

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return
    replied_id = update.message.reply_to_message.message_id
    reply_text = update.message.text
    data = load_data()

    for msg in data["messages"]:
        if msg["tg_message_id"] == replied_id:
            try:
                await context.bot.send_message(
    msg["user_id"],
    f"*📬 تم الرد على صراحتك:*\n\n{reply_text}\n\n_شكرًا لمشاركتك وثقتك بنا._",
    parse_mode="Markdown"
                )
                msg["reply"] = reply_text
                save_data(data)
                await update.message.reply_text("✅ تم إرسال الرد للمستخدم وتوثيقه بنجاح.")
            except:
                await update.message.reply_text("⚠️ تعذر إرسال الرد — قد يكون المستخدم حظر البوت أو غير متاح.")
            return
    await update.message.reply_text("❌ تعذّر تحديد صاحب الصراحة — قد تكون قديمة أو محذوفة.")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query.from_user.id != OWNER_ID:
        return await update.callback_query.answer("🚫 عذرًا، صلاحية هذا الزر محصورة بمالك البوت فقط.")
    context.user_data["broadcast_mode"] = True
    await update.callback_query.message.reply_text("📝 أرسل الآن نص أو صورة للإذاعة.")

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("broadcast_mode"):
        return
    context.user_data["broadcast_mode"] = False
    data = load_data()
    users = data["users"]
    text = update.message.caption or update.message.text
    success = 0

    for uid in users:
        try:
            if update.message.photo:
                await context.bot.send_photo(
                    uid,
                    update.message.photo[-1].file_id,
                    caption=f"📢 *وصلتك رسالة جديدة من إدارة البوت:*\n\n{text}\n\n— فريق إدارة البوت 🤖",
                    parse_mode="Markdown"
                )
            else:
                await context.bot.send_message(
                    uid,
                    f"📢 *وصلتك رسالة جديدة من إدارة البوت:*\n\n{text}\n\n— فريق إدارة البوت 🤖",
                    parse_mode="Markdown"
                )
            success += 1
        except:
            continue

    await update.message.reply_text(
        f"📡 تم إرسال الإذاعة بنجاح.\n📬 وُزّعت على {success} من {len(users)} مستخدم مسجّل."
    )

# 🧠 أولاً: عرف دالة main()
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.REPLY & filters.TEXT & filters.User(user_id=OWNER_ID), handle_reply))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(user_id=OWNER_ID), handle_broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_confession))
    print("✅ البوت شغال بكل أناقة!")
    app.run_polling()

# 🌐 ثم: عرف keep_alive()
def keep_alive():
    app = Flask('')
    @app.route('/')
    def home():
        return "I'm alive!"
    def run():
        app.run(host='0.0.0.0', port=8080)
    threading.Thread(target=run).start()

# 🚀 وأخيرًا: استدعِهم بهذا الترتيب بالضبط
if __name__ == '__main__':
    keep_alive()
    main()