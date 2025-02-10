from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from config import TOKEN
from handlers.black_list import handle_blacklist_button
from handlers.commands import start_command, help_command, custom_command
from handlers.contact import contact_handler
from handlers.input import handle_input
from handlers.messages import handle_message
from handlers.event_booking import handle_book_event
from handlers.event_delete import handle_cancel_event
from handlers.event_edit import handle_edit_event
from handlers.event import handle_create_event, handle_calendar_selection, handle_check_schedule, \
    handle_event_selection, handle_time_selection, handle_cancel_booking, handle_show_event_details
from handlers.send_message import handle_send_message
from handlers.user import handle_user_selection, handle_see_past_events, handle_upcoming_bookings
from utils.roles import send_role_based_menu

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))
    # This handler checks if user exists and register if not
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))

    # Main menu
    app.add_handler(CallbackQueryHandler(send_role_based_menu, pattern="^main_menu$"))

    # Creating event
    app.add_handler(CallbackQueryHandler(handle_create_event, pattern='^create_event$'))
    app.add_handler(CallbackQueryHandler(handle_calendar_selection, pattern=r"day_\d+"))
    app.add_handler(CallbackQueryHandler(handle_time_selection, pattern=r"^(hour_\d{1,2}|minute_\d{1,2}|select_minutes)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))

    # Check events
    app.add_handler(CallbackQueryHandler(handle_check_schedule, pattern="check_schedule"))
    app.add_handler(CallbackQueryHandler(handle_event_selection, pattern=r"event_\d+"))

    # Book event
    app.add_handler(CallbackQueryHandler(handle_book_event, pattern=r"book_event_\d+"))

    # Cancel booking
    app.add_handler(CallbackQueryHandler(handle_cancel_booking, pattern=r"cancel_booking_\d+"))

    #See past bookings
    app.add_handler(CallbackQueryHandler(handle_see_past_events, pattern="see_past_events"))

    # My bookings
    app.add_handler(CallbackQueryHandler(handle_upcoming_bookings, pattern="upcoming_bookings"))

    # Edit event
    app.add_handler(CallbackQueryHandler(handle_edit_event, pattern=r"^edit_event_\d+$"))  # Add this line for edit functionality

    # Cancel event
    app.add_handler(CallbackQueryHandler(handle_cancel_event, pattern=r"^cancel_event_\d+$"))

    # Show details of the event (who is booked)
    app.add_handler(CallbackQueryHandler(handle_show_event_details, pattern=r"^show_event_details_\d+$"))

    # Handle user selection when see it in event vew details
    app.add_handler(CallbackQueryHandler(handle_user_selection, pattern=r'^user_details_\d+$'))

    # Handle send message to user
    app.add_handler(CallbackQueryHandler(handle_send_message, pattern=r"^send_message_\d+$"))

    # Handle add to black list
    app.add_handler(CallbackQueryHandler(handle_blacklist_button, pattern=r"^add_blacklist_\d+$"))

    # Keep this at the end to handle all messages which were not handled above
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print('Polling...')
    app.run_polling()
    # test