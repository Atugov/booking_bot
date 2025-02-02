from telegram import Update

from config import BOT_USERNAME


async def handle_message(update: Update, context):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    response: str = handle_response(text) if message_type != 'group' or BOT_USERNAME not in text else handle_response(text.replace(BOT_USERNAME, '').strip())

    await update.message.reply_text(response)

def handle_response(text: str) -> str:
    processed: str = text.lower()
    if 'hello' in processed:
        return 'Hey there'
    if 'how are you' in processed:
        return 'I am good'
    if 'i love metro' in processed:
        return 'Me too'
    return 'I do not get it'