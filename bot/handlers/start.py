from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.keyboards.markups import keyboard_markup_start

REDIRECT_FROM_TRACKING_KEY = "redirect_from_tracking"


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for /start command.
    """
    if not update.message and not update.callback_query:
        return

    redirect_from_tracking = False
    if context.user_data is not None:
        redirect_from_tracking = str(context.user_data.get(REDIRECT_FROM_TRACKING_KEY)) == "True"
        context.user_data.clear()

    start_msg = "\n".join(
        [
            "سلام",
            "به ربات *رهگیری مرسولات پستی* خوش آمدی! \n",
            "📌 *چطور کار می‌کنه؟* \n",
            "📦 با وارد کردن شماره رهگیری مرسوله پستی، اطلاعات رهگیری مرسوله را از ربات دریافت کنید. \n",
        ]
    )

    if redirect_from_tracking:
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=start_msg,
                reply_markup=keyboard_markup_start,
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        if update.message:
            await update.message.reply_text(start_msg, reply_markup=keyboard_markup_start, parse_mode=ParseMode.MARKDOWN)
        elif update.callback_query:
            await update.callback_query.edit_message_text(
                start_msg, reply_markup=keyboard_markup_start, parse_mode=ParseMode.MARKDOWN
            )
