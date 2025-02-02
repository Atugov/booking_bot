from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
import calendar

from app.utils.translations_logic import translate_buttons


# Inline Button Creators
def create_admin_inline_buttons(user_id):
    buttons = [
        {"text": "Create event", "callback_data": "create_event"},
        {"text": "Check schedule", "callback_data": "check_schedule"}
    ]
    translated_buttons = translate_buttons(user_id, buttons)
    return InlineKeyboardMarkup([translated_buttons])


def create_user_inline_buttons(user_id):
    buttons = [
        {"text": "Check schedule", "callback_data": "check_schedule"},
        {"text": "See past bookings", "callback_data": "see_past_events"},
        {"text": "My bookings", "callback_data": "upcoming_bookings"}
    ]
    translated_buttons = translate_buttons(user_id, buttons)
    return InlineKeyboardMarkup([translated_buttons])


def create_superadmin_inline_buttons(user_id):
    buttons = [
        {"text": "Manage users", "callback_data": "manage_users"},
        {"text": "Create event", "callback_data": "create_event"},
        {"text": "Check schedule", "callback_data": "check_schedule"}
    ]
    translated_buttons = translate_buttons(user_id, buttons)
    return InlineKeyboardMarkup([translated_buttons])


def create_calendar_buttons():
    # Get the current date
    now = datetime.now()

    # Calculate the number of days since the start of the week (Monday)
    days_since_start_of_week = (now.weekday() - calendar.MONDAY) % 7

    # Generate the next 35 days starting from today
    days = [now + timedelta(days=i) for i in range(35)]

    # Adjust the start of the calendar so that today appears correctly
    days_to_display = [None] * days_since_start_of_week + days  # Prepend empty days for the previous week

    # Create the keyboard with 5 rows and 7 columns, ensuring correct start from today
    keyboard = [
        [
            InlineKeyboardButton(
                day.strftime('%d/%m'),  # Format as "DD/MM"
                callback_data=f"day_{day.strftime('%Y-%m-%d')}"
            ) if day else InlineKeyboardButton(" ", callback_data="no_action")  # Fill with empty if None
            for day in days_to_display[i:i + 7]
        ]
        for i in range(0, 35, 7)  # Only iterate over 35 days (5 rows)
    ]

    return InlineKeyboardMarkup(keyboard)

def create_time_buttons():
    hours = [str(hour).zfill(2) for hour in range(0, 24)]  # Create a list of hour values (00, 01, ..., 23)

    # Split the hours list into three parts (6 items in each row)
    row1 = hours[:6]  # First 6 hours (00, 01, ..., 05)
    row2 = hours[6:12]  # Next 6 hours (06, 07, ..., 11)
    row3 = hours[12:18]  # Next 6 hours (12, 13, ..., 17)
    row4 = hours[18:24]  # Next 6 hours (18, 19, ..., 23)

    # Create the InlineKeyboardMarkup with four rows of 6 hour buttons
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(hour, callback_data=f"hour_{hour}") for hour in row1],
        [InlineKeyboardButton(hour, callback_data=f"hour_{hour}") for hour in row2],
        [InlineKeyboardButton(hour, callback_data=f"hour_{hour}") for hour in row3],
        [InlineKeyboardButton(hour, callback_data=f"hour_{hour}") for hour in row4]
    ])

def create_minute_buttons():
    minutes = [str(minute).zfill(2) for minute in
               range(0, 60, 5)]  # Create a list of minute values (00, 05, 10, ..., 55)

    # Split the minutes list into two parts (6 items in each row)
    row1 = minutes[:6]  # First 6 minutes
    row2 = minutes[6:12]  # Next 6 minutes

    # Create the InlineKeyboardMarkup with two rows of 6 minute buttons
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(minute, callback_data=f"minute_{minute}") for minute in row1],
        [InlineKeyboardButton(minute, callback_data=f"minute_{minute}") for minute in row2]
    ])

