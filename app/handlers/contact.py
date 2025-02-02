from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from app.utils.database import save_user_to_db
from app.utils.roles import send_role_based_menu


# Contact Sharing
async def share_contact_command(update, context):
    contact_button = KeyboardButton("Share Phone Number", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Hello! Please share your phone number to continue.", reply_markup=reply_markup)

async def contact_handler(update, context):
    user_id = update.message.from_user.id
    name = update.message.from_user.full_name
    contact = update.message.contact

    if contact:
        phone_number = contact.phone_number

        # Save user to database
        save_user_to_db(user_id, name, phone_number)

        # Send confirmation and menu
        await update.message.reply_text(
            f"Thanks, {name}! Your phone number ({phone_number}) has been saved.",
            reply_markup=ReplyKeyboardRemove()
        )

        # Use the helper function to send the menu
        await send_role_based_menu(update, context, user_id)
    else:
        await update.message.reply_text("Please use the button to share your phone number.")
