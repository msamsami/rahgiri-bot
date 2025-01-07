from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards.markups import keyboard_markup_start

start_msg = "\n".join(
    [
        "سلام",
        "به ربات *رهگیری مرسولات پستی* خوش آمدی! \n",
        "📌 *چطور کار می‌کنه؟* \n",
        "📦 با وارد کردن شماره رهگیری مرسوله پستی، اطلاعات رهگیری مرسوله را از ربات دریافت کنید. \n",
    ]
)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for /start command.
    """
    if not update.message and not update.callback_query:
        return

    if context.user_data is not None:
        context.user_data.clear()

    if update.message:
        await update.message.reply_text(start_msg, reply_markup=keyboard_markup_start, parse_mode="markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(start_msg, reply_markup=keyboard_markup_start, parse_mode="markdown")
