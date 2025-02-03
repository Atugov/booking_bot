from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.utils.database import supabase, check_user_in_db, \
    update_existing_event
from app.utils.keyboard_utils import create_calendar_buttons
from app.utils.keyboard_utils import create_minute_buttons, create_admin_inline_buttons, create_time_buttons
from app.utils.messages import delete_previous_messages
from app.utils.translations_logic import send_translated_message, translate_buttons, t


# Calendar Handling
async def send_calendar(update, context):
    await update.callback_query.message.reply_text("Please select a date:", reply_markup=create_calendar_buttons())

async def handle_create_event(update, context):
    # Set event_mode to 'create'
    context.user_data['event_mode'] = 'create'
    await send_calendar(update, context)

async def handle_calendar_selection(update, context):
    query = update.callback_query
    selected_date = query.data.split('_')[1]  # Extract the selected date in YYYY-MM-DD format

    # Convert the selected date to a datetime object
    try:
        selected_day = datetime.strptime(selected_date, '%Y-%m-%d')
    except ValueError:
        await query.answer("Invalid date selected. Please try again.")
        return

    # Save the selected day in context for later use
    context.user_data['selected_day'] = selected_day
    print(f"Selected day: {selected_day.strftime('%d/%m/%Y')}")

    # Ask the user to select the hour
    await query.answer()
    await query.edit_message_text(f"Please select the hour for {selected_day.strftime('%d/%m/%Y')}:", reply_markup=create_time_buttons())


async def handle_time_selection(update, context):
    query = update.callback_query
    data = query.data

    selected_day = context.user_data.get('selected_day', None)
    if selected_day is None:
        await query.answer("Error: Please select a day first.")
        return

    # Extract year, month, and day from the selected_day datetime object
    selected_year = selected_day.year
    selected_month = selected_day.month
    selected_day = selected_day.day  # Get the day of the month

    if data.startswith("hour_"):
        selected_hour = int(data.split("_")[1])
        context.user_data["selected_hour"] = selected_hour
        print(f"Selected hour: {selected_hour}")

        await query.answer()
        await query.edit_message_text("Please select the minute:", reply_markup=create_minute_buttons())

    elif data.startswith("minute_"):
        selected_minute = int(data.split("_")[1])
        selected_hour = context.user_data.get('selected_hour', None)

        if selected_hour is None or selected_minute is None:
            await query.answer("Error: Please complete the hour and minute selection.")
            return

        # Fix: Use year, month, day extracted above
        now = datetime.now()  # Get the current datetime object
        schedule_time = datetime(selected_year, selected_month, selected_day, selected_hour, selected_minute)

        context.user_data["event_time"] = schedule_time
        print(f"Event time selected: {schedule_time.strftime('%d.%m.%Y %H:%M')}")

        # Handle based on event_mode (create or edit)
        event_mode = context.user_data.get('event_mode', None)
        if event_mode == 'create':
            await query.answer()
            await query.edit_message_text("How many spaces would you like to assign? (Please enter a number)")
            context.user_data['waiting_for_spaces'] = True
        elif event_mode == 'edit':
            # Update existing event in database
            await update_existing_event(schedule_time, context.user_data['editing_schedule'])
            await query.answer()
            await query.edit_message_text(f"Your schedule has been updated to {schedule_time.strftime('%d.%m.%Y %H:%M')}.")
            await query.message.reply_text("Please choose an option:", reply_markup=create_admin_inline_buttons())


async def handle_check_schedule(update, context):
    try:
        await delete_previous_messages(update, context)

        # Get user_id from update
        user_id = update.effective_user.id

        # Step 2: Fetch the current datetime in ISO format
        current_datetime = datetime.now().isoformat()

        # Query only future events
        response = (
            supabase.table('events')
            .select('*')
            .gte('event_datetime', current_datetime)
            .order('event_datetime')
            .execute()
        )

        if response.data:
            # Fetch user's bookings to check which events they have booked
            bookings_response = (
                supabase.table('bookings')
                .select('event_id')
                .eq('user_id', user_id)
                .eq('status', 'confirmed')
                .execute()
            )
            booked_event_ids = {booking['event_id'] for booking in bookings_response.data} if bookings_response.data else set()

            # Create a list of buttons for all future events
            keyboard = []
            for event in response.data:
                event_id = event['event_id']
                spaces = event['spaces']

                # Query the bookings table to count confirmed bookings for this event
                confirmed_bookings_count = (
                    supabase.table('bookings')
                    .select('status')
                    .eq('event_id', event_id)
                    .eq('status', 'confirmed')
                    .execute()
                )
                confirmed_bookings_count = len(confirmed_bookings_count.data) if confirmed_bookings_count.data else 0

                # Calculate spaces left
                spaces_left = spaces - confirmed_bookings_count if spaces is not None else "Spaces not provided"

                # Check if the user has already booked this event
                booked_indicator = " ✅" if event_id in booked_event_ids else ""
                user_data = check_user_in_db(user_id)
                user_language = user_data[0].get("language", "en") if user_data else "en"
                # Add event button with appropriate spaces display
                spaces_display = f"({spaces_left} {t(user_language, 'left')})" if isinstance(spaces_left,
                                                                                             int) else f"({t(user_language, 'Spaces not provided')})"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{datetime.fromisoformat(event['event_datetime']).strftime('%d.%m.%Y %H:%M')} {spaces_display}{booked_indicator}",
                        callback_data=f"event_{event_id}"  # Use the event ID for later actions
                    )
                ])

            # Add "Main Menu" button at the bottom (translated)
            keyboard.append(translate_buttons(user_id, [{"text": "Main Menu", "callback_data": "main_menu"}]))

            # Send the new message with upcoming events
            await update.callback_query.answer()  # Acknowledge the callback
            sent_message = await send_translated_message(
                update, context,
                "Here are the upcoming events:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            # Store the message ID for the main menu message (specific to check_schedule)
            context.user_data["check_schedule_message_id"] = sent_message.message_id

        else:
            await update.callback_query.answer()
            await update.callback_query.message.reply_text("There are no upcoming events.")

    except Exception as e:
        print(f"Error during schedule check: {e}")
        await update.callback_query.message.reply_text(
            "An error occurred while checking the schedule. Please try again."
        )



async def handle_event_selection(update, context):
    await delete_previous_messages(update, context)
    user_id = update.callback_query.from_user.id
    event_id = update.callback_query.data.split('_')[1]  # Extract event ID
    user_data = check_user_in_db(user_id)

    if not user_data:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("User not found. Please register first.")
        return

    role_id = user_data[0].get('role_id')

    # Fetch event details from the database
    event_response = supabase.table('events').select('*').eq('event_id', event_id).execute()
    if not event_response.data:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("Event not found.")
        return

    event = event_response.data[0]
    event_time = datetime.fromisoformat(event['event_datetime']).strftime('%d.%m.%Y %H:%M')
    spaces = event['spaces']

    # Query the bookings table to check if the user has already booked this event
    bookings_response = supabase.table('bookings').select('*').eq('event_id', event_id).execute()

    booked_users_count = len(bookings_response.data)  # Number of users who have booked
    existing_booking = next((booking for booking in bookings_response.data if booking['user_id'] == user_id), None)

    # Check if there's an existing booking or not before proceeding
    if existing_booking:
        booking_id = existing_booking['booking_id']
        button_text = "Cancel Booking"
        callback_data = f"cancel_booking_{booking_id}"
    else:
        button_text = "Book Event"
        callback_data = f"book_event_{event_id}"

    # Prepare the message
    spaces_left = spaces - booked_users_count if booked_users_count < spaces else 0  # If spaces left
    message = f"Time: {event_time}\nSpaces Left: {spaces_left}\n"

    # Prepare buttons based on role
    if role_id == 1 or role_id == 2:  # Admin role
        # Admin actions: Edit, View, Cancel
        buttons = [
            {"text": "Edit event", "callback_data": f"edit_event_{event_id}"},
            {"text": "View details", "callback_data": f"show_event_details_{event_id}"},
            {"text": "Cancel event", "callback_data": f"cancel_event_{event_id}"},
            {"text": f"{button_text}", "callback_data": callback_data},
            {"text": "Main Menu", "callback_data": "main_menu"}

        ]
        translated_buttons = translate_buttons(user_id, buttons)
    else:
        # Regular user actions: Book or Cancel booking
        buttons = [
            {"text": f"{button_text}", "callback_data": callback_data},
            {"text": "Main Menu", "callback_data": "main_menu"}
        ]
        translated_buttons = translate_buttons(user_id, buttons)

    await update.callback_query.answer()  # Acknowledge the callback
    sent_message = await update.callback_query.message.reply_text(message, reply_markup=InlineKeyboardMarkup([translated_buttons]))
    context.user_data["event_selection_message_id"] = sent_message.message_id


async def handle_cancel_booking(update, context):
    await delete_previous_messages(update,context)
    user_id = update.callback_query.from_user.id
    booking_id = update.callback_query.data.split('_')[2]  # 'cancel_booking_123' -> booking_id = 123

    try:
        # Step 1: Check if the booking exists for this booking_id
        bookings_response = supabase.table('bookings').select('*').eq('booking_id', booking_id).execute()

        if bookings_response.data:
            # Get the booking data and user_id from the response
            booking_data = bookings_response.data[0]
            booking_user_id = booking_data['user_id']

            # Step 2: Fetch the requestor's role
            user_response = supabase.table('users').select('role_id').eq('user_id', user_id).execute()
            if not user_response.data:
                await update.callback_query.answer("Unable to verify your role.")
                return

            requestor_role_id = user_response.data[0]['role_id']

            # Check if the requestor is allowed to cancel this booking
            if booking_user_id != user_id and requestor_role_id > 2:  # Non-admins can't cancel other users' bookings
                await update.callback_query.answer("You can only cancel your own booking.")
                return

            # Step 3: Fetch event details
            event_id = booking_data['event_id']
            event_response = supabase.table('events').select('event_datetime').eq('event_id', event_id).execute()
            if not event_response.data:
                await update.callback_query.answer("Event not found.")
                return

            event = event_response.data[0]
            event_datetime = event.get('event_datetime')
            formatted_event_datetime = datetime.fromisoformat(event_datetime).strftime("%d.%m.%Y %H:%M")

            # Step 4: Delete the booking
            delete_response = supabase.table('bookings').delete().eq('booking_id', booking_id).execute()

            # Check for errors in the delete response
            if hasattr(delete_response, 'error') and delete_response.error:
                raise Exception(f"Error canceling booking: {delete_response.error}")

            # Step 5: Fetch the user's name based on booking_user_id
            user_name_response = supabase.table('users').select('name').eq('user_id', booking_user_id).execute()
            if not user_name_response.data:
                user_name = "User"  # Fallback if name is unavailable
            else:
                user_name = user_name_response.data[0]['name']

            # Step 6: Acknowledge cancellation
            await update.callback_query.answer("Booking cancelled successfully!")

            # Step 7: Send a confirmation message with updated options
            buttons = [
                {"text": "Check schedule", "callback_data": "check_schedule"},
                {"text": "Main Menu", "callback_data": "main_menu"}
            ]
            translated_buttons = translate_buttons(user_id, buttons)
            await update.callback_query.message.reply_text(
                f"You have successfully cancelled booking for {user_name} on {formatted_event_datetime}. Message will be sent to user"
            )
            buttons_message = await update.callback_query.message.reply_text("Please choose an option",
                                                                             reply_markup=InlineKeyboardMarkup(translated_buttons)
                                                                             )
            context.user_data["cancellation_booking_buttons_message_id"] = buttons_message.message_id
            # Step 8: Notify the user whose booking was canceled, but ONLY if an admin (role_id 1 or 2) performed the cancellation
            if requestor_role_id in [1, 2] and booking_user_id != user_id:  # Admin canceled someone else's booking
                cancellation_message = f"Your booking on {formatted_event_datetime} has been canceled by Admin."
                try:
                    await context.bot.send_message(chat_id=booking_user_id, text=cancellation_message)
                except Exception as e:
                    print(f"Error sending cancellation notification: {str(e)}")


        else:
            await update.callback_query.answer("Booking not found.")
            await update.callback_query.message.reply_text("Your booking could not be found.")

    except Exception as e:
        print(f"Error during booking cancellation: {e}")
        await update.callback_query.message.reply_text("An error occurred while processing your cancellation.")



async def handle_show_event_details(update, context):
    query = update.callback_query
    event_id = int(query.data.split("_")[-1])  # Extract event_id from the callback data

    try:
        # Step 1: Fetch event details
        event_response = supabase.table("events").select("*").eq("event_id", event_id).execute()
        if not event_response.data:
            await query.answer("Event not found!")
            return

        event = event_response.data[0]  # Get the first result
        event_datetime = event["event_datetime"]
        formatted_event_datetime = datetime.strptime(event_datetime, '%Y-%m-%dT%H:%M:%S').strftime('%d.%m.%Y %H:%M')

        # Step 2: Get users who booked this event
        bookings_response = supabase.table("bookings").select("user_id").eq("event_id", event_id).execute()
        if not bookings_response.data:
            # If no bookings, send a message with main menu and schedule buttons
            keyboard = [
                [InlineKeyboardButton("Main Menu", callback_data="main_menu"),
                InlineKeyboardButton("Check Schedule", callback_data="check_schedule")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.answer()
            await query.edit_message_text(
                f"Nobody booked on {formatted_event_datetime} yet.",
                reply_markup=reply_markup
            )
            return

        user_ids = [booking["user_id"] for booking in bookings_response.data]

        # Step 3: Fetch user details
        users_response = supabase.table("users").select("user_id, name, phone_number").in_("user_id", user_ids).execute()
        users = users_response.data

        # Step 4: Generate buttons for each user
        keyboard = [
            [
                InlineKeyboardButton(
                    text=f"{user['name']} ({user['phone_number']})",
                    callback_data=f"user_details_{user['user_id']}"
                )
            ]
            for user in users
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Step 5: Edit the message to show the user buttons
        await query.answer()
        await query.edit_message_text(
            f"Users booked for the event on {formatted_event_datetime}:",
            reply_markup=reply_markup
        )

    except Exception as e:
        print(f"Error showing event details: {str(e)}")
        await query.answer("An error occurred while fetching event details. Please try again.")


