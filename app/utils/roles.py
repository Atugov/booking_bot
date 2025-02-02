from app.utils.database import check_user_in_db
from app.utils.keyboard_utils import create_superadmin_inline_buttons, create_admin_inline_buttons, \
    create_user_inline_buttons
from app.utils.messages import delete_previous_messages
from app.utils.translations_logic import send_translated_message


async def send_role_based_menu(update, context, welcome: bool = False):
    await delete_previous_messages(update, context)

    # Check if the update has callback_query or message
    if update.callback_query:
        user_id = update.callback_query.from_user.id  # Get user_id from the callback
        message = update.callback_query.message
    else:
        user_id = update.message.from_user.id  # For normal messages (like start command)
        message = update.message

    # Fetch user data from the database
    user_data = check_user_in_db(user_id)
    if user_data:
        role_id = user_data[0].get('role_id')
        name = user_data[0].get('name')  # Fetch name from DB
    else:
        await message.reply_text("User not found in the database. Please register first.")
        return

    # Send welcome message only if the flag is set to True (for `/start` command)
    if welcome and name:
        sent_message = await send_translated_message(update, context, "Welcome back, {name}!", name=name)
        # Store the welcome message ID in user_data
        context.user_data["welcome_message_id"] = sent_message.message_id
        print(f'welcome_message_id: {sent_message.message_id}')
    # Show menu based on role
    if role_id == 1:  # Superadmin
        reply_markup = create_superadmin_inline_buttons(user_id)
    elif role_id == 2:  # Admin
        reply_markup = create_admin_inline_buttons(user_id)
    else:  # Regular User
        reply_markup = create_user_inline_buttons(user_id)

    # Send menu options
    sent_message = await send_translated_message(update, context, "Please choose an option:", reply_markup=reply_markup)
    # Store the menu message ID in user_data
    context.user_data["menu_message_id"] = sent_message.message_id
    print(f'menu_message_id: {sent_message.message_id}')






