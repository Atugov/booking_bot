from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.utils.database import check_user_in_db
from app.utils.translations import translations


def t(user_language, key, **kwargs):
    # Safely fetch the translation or fallback to 'en' if the key/language is missing
    translation = translations.get(key, {}).get(user_language, translations.get(key, {}).get("en", key))
    return translation.format(**kwargs) if translation else key



async def send_translated_message(update, context, key, **kwargs):
    user_id = update.effective_user.id
    user_data = check_user_in_db(user_id)
    user_language = user_data[0].get("language", "en") if user_data else "en"
    print(f'key: {key}')
    message_text = t(user_language, key, **kwargs)
    print(f'message_text: {message_text}')
    reply_markup = kwargs.get("reply_markup", None)

    # Handle both normal messages and callback queries
    if update.message:
        return await update.message.reply_text(message_text, reply_markup=reply_markup)
    elif update.callback_query:
        return await update.callback_query.message.reply_text(message_text, reply_markup=reply_markup)
    else:
        print("Error: Neither update.message nor update.callback_query.message exists.")
        return None  # Return None to prevent crashes

def translate_buttons(user_id, buttons):
    user_data = check_user_in_db(user_id)
    user_language = user_data[0].get("language", "en") if user_data else "en"
    return [
        InlineKeyboardButton(t(user_language, button["text"]), callback_data=button["callback_data"])
        for button in buttons
    ]