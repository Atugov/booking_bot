from telegram import ForceReply

from app.utils.database import supabase
from app.utils.roles import send_role_based_menu


async def handle_send_message(update, context):
    query = update.callback_query
    user_id = int(query.data.split("_")[2])  # Extract user_id from callback data

    # Ask the admin for the message text
    await query.answer()
    await query.message.reply_text(
        "Please type the message you want to send:",
        reply_markup=ForceReply(selective=True)
    )
    context.user_data['send_message_to_user'] = True
    # Save the user_id in the context for reference
    context.user_data["target_user_id"] = user_id

async def handle_send_message_to_user(update, context):
    # Check if the message is a reply
    if not update.message.reply_to_message:
        await update.message.reply_text("Please reply to a specific message.")
        return

    # Retrieve the user_id from context
    target_user_id = context.user_data.get("target_user_id")
    if not target_user_id:
        await update.message.reply_text("No user specified for sending the message.")
        return

    message_text = update.message.text  # Get the admin's typed message

    # Query the users table to get the name and phone number of the target user
    user_response = supabase.table('users').select('name', 'phone_number').eq('user_id', target_user_id).execute()

    if not user_response.data:
        await update.message.reply_text("Could not find the user details.")
        return

    user = user_response.data[0]
    user_name = user.get('name', 'Unknown User')
    user_phone = user.get('phone_number', 'Unknown Phone Number')

    try:
        # Send the message to the target user
        await context.bot.send_message(chat_id=target_user_id, text=message_text)
        await update.message.reply_text(
            f"Message successfully sent to {user_name} with phone number {user_phone}."
        )
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        await update.message.reply_text("An error occurred while sending the message.")

    # After sending the message, redirect the user to the role-based menu
    await send_role_based_menu(update, context)


