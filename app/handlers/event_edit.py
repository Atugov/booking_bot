import calendar
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from app.handlers.event import send_calendar
from app.utils.database import supabase


async def handle_edit_event(update, context):
    # Set event_mode to 'edit' and store the event ID
    schedule_id = int(update.callback_query.data.split('_')[2])
    context.user_data['event_mode'] = 'edit'
    context.user_data['editing_schedule'] = schedule_id
    await send_calendar(update, context)


async def handle_day_selection(update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split("_")
    day = int(data[2])  # Extract the selected day
    schedule_id = int(data[3])  # Extract the schedule ID

    # Update the schedule with the new selected day (implement your schedule updating logic here)
    print(f"Selected Day: {day}, Schedule ID: {schedule_id}")

    # Confirm the change
    await query.edit_message_text(f"Schedule updated to: {day}/{datetime.now().month}/{datetime.now().year}")

    # Optionally, send the user back to the main menu
    await query.answer()


async def handle_new_day_selection(update, context):
    try:
        # Ensure schedule_id is available from the callback data (split correctly)
        callback_data = update.callback_query.data.split('_')
        schedule_id = int(callback_data[2])  # schedule_id is the 3rd part
        new_day = int(callback_data[3])  # new_day is the 4th part

        # Query the database for the selected schedule
        response = supabase.table('schedule').select('*').eq('id', schedule_id).execute()

        if response.data:
            schedule = response.data[0]
            schedule_time = datetime.fromisoformat(schedule['schedule_time'])

            # Get the last valid day of the month for the given schedule_time
            _, last_day_of_month = calendar.monthrange(schedule_time.year, schedule_time.month)

            if new_day > last_day_of_month:
                await update.callback_query.message.reply_text(f"The day {new_day} is invalid for {schedule_time.strftime('%B')} {schedule_time.year}. Please choose a valid day.")
                return

            # Replace the day in the schedule_time with the new valid day
            updated_schedule_time = schedule_time.replace(day=new_day)

            # Save the updated schedule back to the database
            supabase.table('schedule').update({"schedule_time": updated_schedule_time.isoformat()}).eq('id', schedule_id).execute()

            # Create the inline keyboard buttons for "Create", "Check Schedule", and "Change Hour"
            keyboard = [
                [InlineKeyboardButton("Create", callback_data="create_event")],
                [InlineKeyboardButton("Check Schedule", callback_data="check_schedule")],
                [InlineKeyboardButton("Change Hour", callback_data=f"change_hour_{schedule_id}")],
            ]

            # Inform the user that the schedule has been updated and show the buttons
            await update.callback_query.message.reply_text(
                f"Your schedule has been updated to {updated_schedule_time.strftime('%d.%m.%Y %H:%M')}.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        else:
            await update.callback_query.message.reply_text("No schedule found with the given ID.")

    except Exception as e:
        print(f"Error during day selection: {e}")
        await update.callback_query.message.reply_text("An error occurred while selecting the day. Please try again.")

