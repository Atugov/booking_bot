from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.utils.database import supabase
from app.utils.keyboard_utils import create_user_inline_buttons
from app.utils.messages import delete_previous_messages
from app.utils.translations_logic import send_translated_message, translate_buttons


async def handle_user_selection(update, context):
    query = update.callback_query
    callback_data = query.data  # e.g., "user_details_123"

    # Parse the callback data
    try:
        _, _, user_id = callback_data.split("_")  # Extract the user_id
        user_id = int(user_id)
    except ValueError:
        await query.answer("Invalid callback data!", show_alert=True)
        return

    # Fetch user details from the database
    user_data = supabase.table("users").select("*").eq("user_id", user_id).execute()
    user_details = user_data.data[0] if user_data.data else None

    # Fetch booking details (to get booking_id)
    booking_data = supabase.table("bookings").select("booking_id").eq("user_id", user_id).execute()
    booking_id = booking_data.data[0]["booking_id"] if booking_data.data else None

    if user_details and booking_id:
        name = user_details.get("name", "N/A")
        phone_number = user_details.get("phone_number", "N/A")

        # Display action buttons for the selected user
        buttons = [
            [
                InlineKeyboardButton("Cancel booking", callback_data=f"cancel_booking_{booking_id}"),
                InlineKeyboardButton("Send Message", callback_data=f"send_message_{user_id}"),
                InlineKeyboardButton("Add to Blacklist", callback_data=f"add_blacklist_{user_id}"),
            ],
            [InlineKeyboardButton("Main Menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        await query.answer()
        await query.message.reply_text(
            f"User Details:\nName: {name}\nPhone: {phone_number}\n\nChoose an action:",
            reply_markup=reply_markup,
        )
    elif not booking_id:
        await query.answer("Booking not found!", show_alert=True)
    else:
        await query.answer("User not found!", show_alert=True)



async def handle_see_past_events(update, context):
    await delete_previous_messages(update, context)

    user_id = update.callback_query.from_user.id
    current_datetime = datetime.now().isoformat()  # Current date and time in ISO format for comparison

    try:
        # Query the bookings table for events booked by the user
        bookings_response = supabase.table('bookings').select('event_id').eq('user_id', user_id).execute()

        if not bookings_response.data:
            sent_message = await send_translated_message(update, context,
                "You have no past events.",
                reply_markup=create_user_inline_buttons(user_id)
            )
            context.user_data["past_events_message_id"] = sent_message.message_id
            return

        # Extract event IDs from bookings
        booked_event_ids = [booking['event_id'] for booking in bookings_response.data]

        # Query the events table for events in the past
        events_response = (
            supabase.table('events')
            .select('event_id, event_datetime, name, location')
            .in_('event_id', booked_event_ids)
            .lte('event_datetime', current_datetime)
            .execute()
        )

        if not events_response.data:
            sent_message = await send_translated_message(update, context,
                "You have no past events.",
                reply_markup=create_user_inline_buttons(user_id)
            )
            context.user_data["past_events_message_id"] = sent_message.message_id
            return

        # Format the past events into a readable message
        formatted_past_events = []
        for event in events_response.data:
            event_date = event.get('event_datetime')
            event_name = event.get('name')
            event_location = event.get('location')

            # Construct event details while skipping None fields
            event_details = []
            if event_date:
                event_details.append(datetime.fromisoformat(event_date).strftime('%d.%m.%Y %H:%M'))
            if event_name:
                event_details.append(event_name)
            if event_location:
                event_details.append(f"at {event_location}")

            # Join the available details for the event
            formatted_past_events.append(" - ".join(event_details))

            # Display the past events
            if formatted_past_events:
                events_message = "\n".join(formatted_past_events)
                sent_message = await update.callback_query.message.reply_text(
                    f"Your Past Events:\n\n{events_message}",
                    reply_markup=create_user_inline_buttons(user_id)
                )
                # Save the message ID for later deletion
                context.user_data["past_events_message_id"] = sent_message.message_id
            else:
                sent_message = await update.callback_query.message.reply_text(
                    "No past events found.",
                    reply_markup=create_user_inline_buttons(user_id)
                )
                # Save the message ID for later deletion
                context.user_data["past_events_message_id"] = sent_message.message_id

    except Exception as e:
        print(f"Error fetching past events: {e}")
        await update.callback_query.message.reply_text("An error occurred while fetching past events.")



async def handle_upcoming_bookings(update, context):
    await delete_previous_messages(update, context)
    user_id = update.callback_query.from_user.id
    current_datetime = datetime.now().isoformat()  # Current date and time in ISO format for comparison

    try:
        # Query the bookings table to find all future events booked by the user
        bookings_response = (
            supabase.table("bookings")
            .select("event_id, status")
            .eq("user_id", user_id)
            .execute()
        )

        if not bookings_response.data:
            sent_message = await update.callback_query.message.reply_text(
                "You have no upcoming bookings.",
                reply_markup=create_user_inline_buttons(user_id)
            )
            context.user_data["upcoming_bookings_message_id"] = sent_message.message_id
            return

        # Extract event IDs for confirmed bookings
        booked_event_ids = [
            booking["event_id"]
            for booking in bookings_response.data
            if booking["status"] == "confirmed"
        ]

        if not booked_event_ids:
            sent_message = await update.callback_query.message.reply_text(
                "You have no confirmed upcoming bookings.",
                reply_markup=create_user_inline_buttons(user_id)
            )
            context.user_data["upcoming_bookings_message_id"] = sent_message.message_id
            return

        # Query the events table to fetch details of future events
        events_response = (
            supabase.table("events")
            .select("event_id, event_datetime, name, location")
            .in_("event_id", booked_event_ids)
            .gte("event_datetime", current_datetime)
            .execute()
        )

        if not events_response.data:
            sent_message = await update.callback_query.message.reply_text(
                "You have no upcoming bookings.",
                reply_markup=create_user_inline_buttons(user_id)
            )
            context.user_data["upcoming_bookings_message_id"] = sent_message.message_id
            return

        # Create a list of buttons for upcoming events
        keyboard = []
        for event in events_response.data:
            event_id = event.get("event_id")
            event_date = event.get("event_datetime")
            event_name = event.get("name")
            event_location = event.get("location")

            # Construct the event button label
            event_details = []
            if event_date:
                event_details.append(datetime.fromisoformat(event_date).strftime('%d.%m.%Y %H:%M'))
            if event_name:
                event_details.append(event_name)
            if event_location:
                event_details.append(f"at {event_location}")

            # Add button to the keyboard
            if event_details:
                button_text = " - ".join(event_details)
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"event_{event_id}")])

        # Add "Main Menu" button at the bottom
        keyboard.append(translate_buttons(user_id, [{"text": "Main Menu", "callback_data": "main_menu"}]))

        # Display the buttons
        sent_message =  await send_translated_message(update, context,
            "Your Upcoming Bookings:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        context.user_data["upcoming_bookings_message_id"] = sent_message.message_id

    except Exception as e:
        print(f"Error fetching upcoming bookings: {e}")
        await update.callback_query.message.reply_text("An error occurred while fetching upcoming bookings.")


