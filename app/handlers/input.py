from app.handlers.black_list import add_user_to_blacklist
from app.handlers.send_message import handle_send_message_to_user
from app.utils.database import save_event_to_db, update_event_spaces
from app.utils.keyboard_utils import create_admin_inline_buttons


async def handle_input(update, context):
    if context.user_data.get('waiting_for_spaces', False):
        await handle_spaces_input(update, context)
    elif context.user_data.get('send_message_to_user', False):
        await handle_send_message_to_user(update, context)
    elif context.user_data.get('blacklist_reason', False):
        await add_user_to_blacklist(update, context)
    else:
        await update.message.reply_text("I don't understand that. Please try again.")

async def handle_spaces_input(update, context):
    user_input = update.message.text.strip()

    if user_input.isdigit():  # Validate numeric input
        spaces = int(user_input)

        if spaces > 0:
            event_time = context.user_data.get("event_time", None)

            if event_time is None:
                await update.message.reply_text("Error: Schedule time not found. Please start over.")
                context.user_data['waiting_for_spaces'] = False
                return

            # Save or update the event in the database
            if context.user_data['event_mode'] == 'create':
                save_event_to_db(event_time, spaces)
                await update.message.reply_text(
                    f"Successfully assigned {spaces} spaces for {event_time.strftime('%d.%m.%Y %H:%M')}.")
            elif context.user_data['event_mode'] == 'edit':
                # Update existing event spaces
                await update_event_spaces(event_time, spaces, context.user_data['editing_schedule'])
                await update.message.reply_text(
                    f"Successfully updated spaces for {event_time.strftime('%d.%m.%Y %H:%M')}.")

            # Reset the flag and clean up context
            context.user_data['waiting_for_spaces'] = False
            context.user_data.pop("event_time", None)

            await update.message.reply_text("Please choose an option:", reply_markup=create_admin_inline_buttons())
        else:
            await update.message.reply_text("Please enter a positive number.")
    else:
        await update.message.reply_text("Invalid input. Please enter a valid number.")


