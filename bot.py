import os
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === CONFIG ===
BOT_TOKEN = "8189030419:AAFKA4GyyPxkurFRlNa_2swM-0sy831XceU"
ADMIN_CHAT_ID = 6832347608  # Your personal numeric ID (not username) - the chat where you want to receive screenshots
UPI_PAYMENT_LINK = "https://tinyurl.com/3kce3yxp"
DRIVE_LINK = "https://drive.google.com/drive/folders/1nVV9Yx52bJNXy04jvrbdgPHlUvsSb0vv?usp=drive_link"

# Environment variables for webhook (when deployed)
PORT = int(os.environ.get('PORT', 4000))
APP_URL = os.environ.get('APP_URL', None)  # Should be set in Render.com environment variables

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
    username = update.message.from_user.username or "Unknown"
    first_name = update.message.from_user.first_name or "Unknown"
    number_to_user[payment_counter] = user_id

    keyboard = [
        [
            InlineKeyboardButton(f"✅ Accept #{payment_counter}", callback_data=f"accept_{payment_counter}"),
            InlineKeyboardButton(f"❌ Decline #{payment_counter}", callback_data=f"decline_{payment_counter}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = f"📩 Payment Screenshot #{payment_counter}\nUser ID: {user_id}\nUsername: @{username}\nName: {first_name}"

    try:
        # Forward the screenshot to admin's private chat with the bot
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo,
            caption=caption,
            reply_markup=reply_markup
        )
        
        # Tell the user their screenshot was received
        await update.message.reply_text("📤 Your payment screenshot has been received. Please wait while we verify your payment.")
    except Exception as e:
        logger.error(f"Error forwarding photo to admin: {e}")
        await update.message.reply_text("⚠️ There was an issue processing your payment. Please try again later.")

    payment_counter += 1

# Callback handler for Accept/Decline buttons
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, number = query.data.split("_")
    number = int(number)

    if number in number_to_user:
        user_id = number_to_user[number]

        try:
            if action == "accept":
                # Send drive link to the original user in their private chat with the bot
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ Payment approved! 🎉\n\nHere's your reels drive link:\n{DRIVE_LINK}"
                )
                # Update message in admin chat to show it was approved
                await query.edit_message_caption(caption=f"✅ Payment #{number} Approved and link sent to user.")

            elif action == "decline":
                # Notify user that payment was declined
                await context.bot.send_message(
                    chat_id=user_id,
                    text="❌ Payment verification failed.\nPlease try again or contact support at zolredine@gmail.com for assistance."
                )
                # Update message in admin chat
                await query.edit_message_caption(caption=f"❌ Payment #{number} Declined and user notified.")

            # Remove entry from mapping
            del number_to_user[number]
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            await query.edit_message_caption(caption=f"⚠️ Error processing payment #{number}: {str(e)}")

    else:
        await query.edit_message_caption(caption="⚠️ This payment number was already processed or is invalid.")


# Error logging
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # Notify about errors that might need immediate attention
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "An error occurred while processing your request. Our team has been notified."
            )
    except:
        pass

# Main function
def main():
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_error_handler(error_handler)

    # Start the Bot
    if APP_URL:
        # Use webhook mode for production (like on Render.com)
        webhook_url = f"{APP_URL}/{BOT_TOKEN}"
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=webhook_url
        )
        logger.info(f"Bot started in webhook mode on port {PORT}")
        logger.info(f"Webhook URL: {webhook_url}")
    else:
        # Use polling for local development
        application.run_polling(drop_pending_updates=True)
        logger.info("Bot started in polling mode")

if __name__ == "__main__":
    main()
