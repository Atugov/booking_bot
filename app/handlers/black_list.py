from app.utils.database import supabase
from app.utils.roles import send_role_based_menu



async def handle_blacklist_button(update, context):
    callback_data = update.callback_query.data
    user_id = callback_data.split("_")[2]  # Extract user_id from callback data

    # Ask admin to enter a reason for blacklisting the user
    context.user_data['target_user_id'] = user_id
    context.user_data['blacklist_reason'] = True
    await update.callback_query.answer()  # Acknowledge the callback
    await update.callback_query.message.reply_text("Please provide a reason for blacklisting this user.")


async def add_user_to_blacklist(update, context):
    # Retrieve the user ID and reason from the context
    user_id = context.user_data.get('target_user_id')
    reason = update.message.text.strip()

    if not user_id:
        await update.message.reply_text("No user specified for blacklisting.")
        return

    if not reason:
        await update.message.reply_text("Please provide a valid reason for blacklisting.")
        return

    # Query the users table to make sure the user exists
    user_response = supabase.table('users').select('name').eq('user_id', user_id).execute()

    if not user_response.data:
        await update.message.reply_text("User not found.")
        return

    user = user_response.data[0]
    user_name = user.get('name', 'Unknown User')

    # Add the user to the blacklist in the database
    try:
        # Insert into the black_lists table
        supabase.table('black_lists').insert({'user_id': user_id, 'note': reason}).execute()
        await update.message.reply_text(f"User {user_name} has been blacklisted with the following reason: {reason}.")
    except Exception as e:
        print(f"Error adding to blacklist: {str(e)}")
        await update.message.reply_text("An error occurred while blacklisting the user.")

    # Reset the target_user_id from context
    context.user_data.pop('target_user_id', None)

    # After blacklisting, send the admin back to the role-based menu
    await send_role_based_menu(update, context)