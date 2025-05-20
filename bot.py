import os
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
)
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# === CONFIG ===
BOT_TOKEN = "8189030419:AAEK_3rpq2LgTwSutDaZrf_eK-uPmjLYJZ0"
ADMIN_CHAT_ID = "snjy13"  # Replace with your Telegram user ID as string
UPI_PAYMENT_LINK = "upi://pay?pa=sanjayrajamani01@okicici&pn=zolredine&am=30.00&cu=INR"

DRIVE_LINK = "https://drive.google.com/drive/folders/1nVV9Yx52bJNXy04jvrbdgPHlUvsSb0vv?usp=drive_link"

# Counter to number each screenshot (in-memory — resets if bot restarts)
payment_counter = 1

# Mapping to track which user submitted which number
number_to_user = {}

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 Pay Here 🔥", url=UPI_PAYMENT_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome!\n\nTo get exclusive reels link:\n\n"
        "1️⃣ Click below to pay via UPI.\n"
        "2️⃣ Send me the payment screenshot here.\n"
        "3️⃣ Wait for approval ✅",
        reply_markup=reply_markup
    )

# Handler for images/screenshots
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global payment_counter

    photo = update.message.photo[-1].file_id
    user_id = update.message.from_user.id
    number_to_user[payment_counter] = user_id

    keyboard = [
        [
            InlineKeyboardButton(f"✅ Accept #{payment_counter}", callback_data=f"accept_{payment_counter}"),
            InlineKeyboardButton(f"❌ Decline #{payment_counter}", callback_data=f"decline_{payment_counter}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = f"📩 Payment Screenshot #{payment_counter}\nUser ID: {user_id}"

    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=photo,
        caption=caption,
        reply_markup=reply_markup
    )

    await update.message.reply_text("📤 Please wait while we verify your payment.")

    payment_counter += 1

# Callback handler for Accept/Decline buttons
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, number = query.data.split("_")
    number = int(number)

    if number in number_to_user:
        user_id = number_to_user[number]

        if action == "accept":
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Payment approved! 🎉\n\nHere’s your reels drive link:\n{DRIVE_LINK}"
            )
            await query.edit_message_caption(caption=f"✅ Payment #{number} Approved.")

        elif action == "decline":
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Payment verification failed.\nPlease try again or contact support at zolredine@gmail.com."
            )
            await query.edit_message_caption(caption=f"❌ Payment #{number} Declined.")

        # Remove entry from mapping
        del number_to_user[number]

    else:
        await query.edit_message_caption(caption="⚠️ This payment number was already processed.")

# Error logging
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)

# Main function
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_error_handler(error_handler)

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
