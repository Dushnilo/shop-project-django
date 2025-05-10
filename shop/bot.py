import jwt
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler

env = Env()
env.read_env()

TOKEN = env('TELEGRAM_BOT_TOKEN')
SECRET_KEY = env('SECRET_KEY')
SITE_URL = env('SITE_URL')
CACHED_PHOTO_ID = 'AgACAgIAAxkDAAMDZ_pigDrAHfTg3ZFJHXwwQ6EFbbUAAkXwMRu_EdlLNW6gCekSgkwBAAMCAAN4AAM2BA'


async def start(update, context):
    chat_id = update.effective_chat.id
    jwt_token = jwt.encode({'chat_id': int(chat_id)},
                           SECRET_KEY, algorithm='HS256')
    deep_link_url = f"{SITE_URL}/?token={jwt_token}"

    welcome_text = """
✨ *Добро пожаловать...* ✨
    """

    keyboard = [
        [InlineKeyboardButton('🛍️ ОТКРЫТЬ КАТАЛОГ',
                              web_app=WebAppInfo(url=deep_link_url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo=CACHED_PHOTO_ID,
        caption=welcome_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=reply_markup
    )

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.run_polling()
