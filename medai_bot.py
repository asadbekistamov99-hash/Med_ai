import sqlite3
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8621767296:AAEgPpXVik5sI0knpiK-wwHrUNbJhMaBZhc"


def db():
    conn = sqlite3.connect("medai.db")
    conn.row_factory = sqlite3.Row
    return conn


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print("USER ID:", user_id)
    await update.message.reply_text(
        f"✅ MedAI bot ishga tushdi\n\nSizning Telegram ID: {user_id}"
    )


async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    hhmm = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")

    conn = db()
    cur = conn.cursor()

    rows = cur.execute("SELECT * FROM reminders WHERE active=1").fetchall()

    due_rows = []
    for r in rows:
        reminder_time = str(r["hhmm"] or "")
        last_sent_date = str(r["last_sent_date"] or "")
        if reminder_time <= hhmm and last_sent_date != today:
            due_rows.append(r)

    print(f"Tekshirilyapti: {hhmm} | topildi: {len(due_rows)}")

    for r in due_rows:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Ichdim", callback_data=f"took_{r['id']}")]
        ])

        try:
            await context.bot.send_message(
                chat_id=r["user_id"],
                text=f"💊 {r['med']} ichish vaqti!",
                reply_markup=keyboard
            )

            cur.execute(
                "UPDATE reminders SET last_sent_date=? WHERE id=?",
                (today, r["id"])
            )

        except Exception as e:
            print("Yuborishda xato:", e)

    conn.commit()
    conn.close()


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    if data.startswith("took_"):
        reminder_id = int(data.split("_", 1)[1])

        conn = db()
        cur = conn.cursor()

        row = cur.execute("SELECT * FROM reminders WHERE id=?", (reminder_id,)).fetchone()
        if row:
            cur.execute("""
                INSERT INTO doses (user_id, med, hhmm, ts, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                row["user_id"],
                row["med"],
                row["hhmm"],
                datetime.now().isoformat(),
                "took"
            ))
            conn.commit()

        conn.close()
        await query.edit_message_text("✅ Qabul qilindi")


def main():
    if not BOT_TOKEN or BOT_TOKEN == "BU_YERGA_TOKENINGNI_YOZ":
        print("❌ BOT_TOKEN yozilmagan")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    if app.job_queue is None:
        print("❌ JobQueue ishlamayapti")
        return

    app.job_queue.run_repeating(check_reminders, interval=30, first=5)

    print("✅ Reminder tizimi ishlayapti")
    print("🤖 Bot ishga tushdi")
    app.run_polling()


if __name__ == "__main__":
    main()
