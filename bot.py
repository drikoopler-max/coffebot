import os
import sqlite3
import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")
DB_NAME = "coffee.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ----------- DB INIT -----------

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER UNIQUE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS drinks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        volume INTEGER,
        category TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        price_per_kg REAL,
        unit TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS drink_ingredients (
        drink_id INTEGER,
        ingredient_id INTEGER,
        amount REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cafe_settings (
        user_id INTEGER PRIMARY KEY,
        salary_per_hour REAL,
        overhead_month REAL,
        cups_per_month INTEGER,
        packaging_cost REAL
    )
    """)

    conn.commit()
    conn.close()

# ----------- HELPERS -----------

def get_user_id(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE telegram_id=?", (telegram_id,))
    row = cur.fetchone()

    if not row:
        cur.execute("INSERT INTO users (telegram_id) VALUES (?)", (telegram_id,))
        conn.commit()
        user_id = cur.lastrowid
    else:
        user_id = row[0]

    conn.close()
    return user_id

# ----------- STATES -----------

(
    ADD_DRINK_NAME,
    ADD_DRINK_VOLUME,
    ADD_DRINK_CATEGORY,
    CALC_MARGIN,
) = range(4)

# ----------- COMMANDS -----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_user_id(update.effective_user.id)

    keyboard = [
        ["➕ Додати напій", "📋 Мої напої"],
        ["💰 Розрахувати ціну"],
        ["🧂 База інгредієнтів", "⚙️ Налаштування"]
    ]
    await update.message.reply_text(
        "☕ Вітаю! Я бот для розрахунку собівартості кавових напоїв.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ----------- ADD DRINK -----------

async def add_drink_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введи назву напою:", reply_markup=ReplyKeyboardRemove())
    return ADD_DRINK_NAME

async def add_drink_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["drink_name"] = update.message.text
    await update.message.reply_text("Обʼєм напою (мл):")
    return ADD_DRINK_VOLUME

async def add_drink_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["drink_volume"] = int(update.message.text)
    await update.message.reply_text("Категорія (кава / чай / інше):")
    return ADD_DRINK_CATEGORY

async def add_drink_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = get_user_id(update.effective_user.id)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO drinks (user_id, name, volume, category)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        context.user_data["drink_name"],
        context.user_data["drink_volume"],
        update.message.text
    ))

    conn.commit()
    conn.close()

    await update.message.reply_text("✅ Напій додано!")
    return ConversationHandler.END

# ----------- CALCULATION -----------

async def calculate_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введи бажану маржу (%) наприклад 70")
    return CALC_MARGIN

async def calc_margin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    margin = float(update.message.text) / 100
    cost = 30.0  # DEMO (можна замінити повним розрахунком)
    price = cost / (1 - margin)

    await update.message.reply_text(
        f"📊 Собівартість: {cost:.2f} грн\n"
        f"💰 Рекомендована ціна: {price:.2f} грн"
    )
    return ConversationHandler.END

# ----------- ERROR -----------

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception:", exc_info=context.error)

# ----------- MAIN -----------

def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    add_drink_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("Додати напій"), add_drink_start)],
        states={
            ADD_DRINK_NAME: [MessageHandler(filters.TEXT, add_drink_name)],
            ADD_DRINK_VOLUME: [MessageHandler(filters.TEXT, add_drink_volume)],
            ADD_DRINK_CATEGORY: [MessageHandler(filters.TEXT, add_drink_category)],
        },
        fallbacks=[],
    )

    calc_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("Розрахувати ціну"), calculate_price)],
        states={
            CALC_MARGIN: [MessageHandler(filters.TEXT, calc_margin)],
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(add_drink_conv)
    app.add_handler(calc_conv)
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
