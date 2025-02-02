async def delete_message_if_exists(bot, chat_id, message_id):
    try:
        if message_id:
            await bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Error deleting message: {e}")




async def delete_previous_messages(update, context):
    message_ids = ["menu_message_id", "welcome_message_id", "past_events_message_id","check_schedule_message_id",
                   "upcoming_bookings_message_id","event_selection_message_id", "confirmation_booking_buttons_message_id",
                   "cancellation_booking_buttons_message_id"]

    for message_id_key in message_ids:
        message_id = context.user_data.get(message_id_key)
        if message_id:
            print(f'Deleting previous message: {message_id} with key: {message_id_key}')
            await delete_message_if_exists(context.bot, update.callback_query.message.chat_id, message_id)
            context.user_data.pop(message_id_key, None)  # Clear the specific message ID

