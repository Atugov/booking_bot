from datetime import datetime

from app.utils.database import delete_related_records, get_event_by_id, \
    delete_event_from_db, log_audit_event
from app.utils.roles import send_role_based_menu


async def handle_cancel_event(update, context):
    query = update.callback_query
    event_id = int(query.data.split("_")[2])  # Extract event_id correctly from the query data

    try:
        # First, check if the event exists in the events table
        event = await get_event_by_id(event_id)  # Fetch the event from the database

        if not event:
            # If the event doesn't exist, notify the user and exit
            await query.answer("Error: The event you are trying to delete does not exist.")
            return

        # Attempt to delete related records from the bookings, waiting lists, and blacklists
        await delete_related_records(event_id)

        # Delete the event from the events table
        await delete_event_from_db(event_id)
        event_datetime = event['event_datetime']  # This should be a datetime string (e.g., '2025-01-24T15:45:00')
        formatted_event_datetime = datetime.strptime(event_datetime, '%Y-%m-%dT%H:%M:%S').strftime('%d.%m.%Y %H:%M')

        # Send confirmation message
        await query.answer()
        await query.edit_message_text(f"Event {formatted_event_datetime} has been successfully canceled.")

        # Optionally, log the deletion in the audit logs
        await log_audit_event('events', event_id, 'DELETE', event, None, query.from_user.id)

        # Show the main menu buttons again after deletion (Create and Check)
        await send_role_based_menu(update, context)

    except Exception as e:
        # Log the error to console for debugging
        print(f"Error during schedule deletion: {str(e)}")

        # Notify the user about the error without showing technical details
        await query.answer("Oops, there was an error while deleting the schedule. Please try again.")


