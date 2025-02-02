from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.utils.database import supabase
from app.utils.messages import delete_previous_messages


async def handle_book_event(update, context):
    await delete_previous_messages(update, context)
    user_id = update.callback_query.from_user.id
    schedule_id = update.callback_query.data.split('_')[2]  # 'book_schedule_123' -> schedule_id = 123

    try:
        # Get the current event from the events table
        response = supabase.table('events').select('event_id', 'spaces', 'event_datetime').eq('event_id', schedule_id).execute()

        if response.data:
            event = response.data[0]  # Get the event details

            # Get the number of spaces available
            spaces = event['spaces']

            # Query the bookings table to check how many users have already booked this event
            bookings_response = supabase.table('bookings').select('*').eq('event_id', schedule_id).execute()

            booked_users_count = len(bookings_response.data)  # Number of users who have booked

            # Calculate the remaining spaces
            spaces_left = spaces - booked_users_count if spaces else "Unlimited"  # If spaces is None, assume unlimited spaces

            # Check if the user has already booked this schedule
            existing_booking = next((booking for booking in bookings_response.data if booking['user_id'] == user_id), None)
            if existing_booking:
                await update.callback_query.answer("You have already booked this schedule!")
                return

            # Add the booking for the user
            booking_data = {
                'event_id': schedule_id,
                'user_id': user_id,
                'payment_status': 'pending',  # Initial payment status, can be updated later
                'amount': 0.00,  # Set default amount for now
                'status': 'confirmed',  # Booking status
                'created_by': user_id,  # Assuming the user is the one booking
                'updated_by': user_id  # Assuming the user is the one booking
            }

            # Insert booking into the bookings table
            booking_response = supabase.table('bookings').insert(booking_data).execute()

            # Log the entire response object for debugging
            print(f"Booking Response: {booking_response}")

            # Check for errors in the booking response
            if hasattr(booking_response, 'error') and booking_response.error:
                raise Exception(f"Error booking schedule: {booking_response.error}")

            # Acknowledge the booking
            await update.callback_query.answer("Schedule booked successfully!")
            event_datetime = event.get('event_datetime')  # Extract 'event_datetime'
            formatted_datetime = datetime.fromisoformat(event_datetime).strftime("%d.%m.%Y %H:%M")

            # Send a message confirming the booking with a "Check Schedule" button
            keyboard = [
                [InlineKeyboardButton("Cancel booking", callback_data=f"cancel_booking_{schedule_id}"),
                InlineKeyboardButton("Main Menu", callback_data="main_menu"), ]
            ]
            await update.callback_query.message.reply_text(
                f"You have successfully booked for: {formatted_datetime}"
            )
            buttons_message = await update.callback_query.message.reply_text("Please choose an option",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            context.user_data["confirmation_booking_buttons_message_id"] = buttons_message.message_id
        else:
            await update.callback_query.answer("Event not found.")
            await update.callback_query.message.reply_text("The selected event could not be found.")

    except Exception as e:
        print(f"Error during booking: {e}")
        await update.callback_query.message.reply_text("An error occurred while processing your request.")

