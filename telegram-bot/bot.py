
import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICE, NAME, PHONE, ADDRESS = range(4)
ADMIN_ID = 1066431129

services = {
    "Борьба с грызунами": "от 4 000 ₸",
    "Борьба с насекомыми": "от 5 000 ₸",
    "Борьба с микробами": "от 6 000 ₸",
}

reply_keyboard = [[service] for service in services]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
phone_button = KeyboardButton("📱 Отправить номер телефона", request_contact=True)
phone_markup = ReplyKeyboardMarkup([[phone_button]], one_time_keyboard=True, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Здравствуйте! Пожалуйста, выберите услугу из списка:", reply_markup=markup)
    return SERVICE

async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = update.message.text
    if service not in services:
        await update.message.reply_text("Пожалуйста, выберите услугу из списка:", reply_markup=markup)
        return SERVICE
    context.user_data["service"] = service
    await update.message.reply_text("Как вас зовут?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Пожалуйста, отправьте ваш номер телефона.", reply_markup=phone_markup)
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if contact:
        phone_number = contact.phone_number
    else:
        phone_number = update.message.text
    context.user_data["phone"] = phone_number
    await update.message.reply_text("Укажите ваш адрес.")
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text
    service = context.user_data["service"]
    name = context.user_data["name"]
    phone = context.user_data["phone"]
    address = context.user_data["address"]
    price = services.get(service, "уточняется")

    await update.message.reply_text(
        f"Спасибо, {name}!
"
        f"Услуга: {service}
"
        f"Номер телефона: {phone}
"
        f"Адрес: {address}
"
        f"Стоимость: {price}

"
        f"Мы свяжемся с вами в ближайшее время!"
    )

    admin_msg = (
        f"📥 Новая заявка:

"
        f"👤 Имя: {name}
"
        f"📞 Телефон: {phone}
"
        f"📍 Адрес: {address}
"
        f"🛠 Услуга: {service}
"
        f"💰 Стоимость: {price}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог отменён. Хорошего дня!")
    return ConversationHandler.END

if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [
                MessageHandler(filters.CONTACT, get_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
            ],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    logger.info("Бот запущен...")
    app.run_polling()
