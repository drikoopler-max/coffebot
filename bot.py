from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8271661677:AAH01Kjj6vYD8ZGYyPn8QQDXxenn7K3iYe4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! Я калькулятор собівартості кави ☕\nНапиши /calc щоб почати розрахунок."
    )

async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введіть собівартість напою (грн):"
    )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("calc", calc))

app.run_polling()
