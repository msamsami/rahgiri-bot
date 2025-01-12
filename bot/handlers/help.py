from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards.markups import keyboard_markup_back


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for the help command.
    """
    if not update.callback_query:
        return

    query = update.callback_query
    await query.answer()

    help_text = "\n".join(
        [
            "📬 ربات تلگرام *رهگیری مرسولات پستی*\n",
            "شما می‌توانید با وارد کردن شماره رهگیری مرسوله، وضعیت ارسال آن را پیگیری کنید.\n",
            "- اطلاعات مربوط به جابجایی مرسولات پستی به صورت لحظه ای در سامانه رهگیری پست ثبت می گردد",
            "- اطلاعات مربوط به مرسولات پستی حداکثر 6 ماه در سامانه رهگیری پست نگهداری و قابل رهگیری می باشد\n",
            "اگر سوالی دارید یا به کمک نیاز دارید، با پشتیبانی تماس بگیرید.",
        ]
    )

    await query.edit_message_text(help_text, reply_markup=keyboard_markup_back, parse_mode="markdown")
