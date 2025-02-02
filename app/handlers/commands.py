from telegram import Update
from telegram.ext import CallbackContext

from app.handlers.contact import share_contact_command
from app.utils.database import check_user_in_db
from app.utils.roles import send_role_based_menu


async def start_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    name = update.message.from_user.full_name
    print(f"User name: {name}")

    # Step 1: Clear all message-related keys from user_data
    message_keys = [key for key in context.user_data if key.endswith("_message_id")]
    for key in message_keys:
        context.user_data.pop(key, None)

    # Check if the user exists in the database
    user = check_user_in_db(user_id)
    if user:
        # If the user exists, welcome them
        await welcome_user(update, context, user, welcome=True)  # Pass `welcome=True`
    else:
        # Prompt the user to share their contact details
        await share_contact_command(update, context)


async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text('I am here to help. Please type something for me to help you.')

async def custom_command(update: Update, context: CallbackContext):
    await update.message.reply_text('This is a custom command.')

async def welcome_user(update: Update, context: CallbackContext, user, welcome: bool = False):
    # Just call send_role_based_menu with the welcome flag
    await send_role_based_menu(update, context, welcome)


