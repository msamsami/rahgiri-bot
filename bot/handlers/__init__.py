from telegram import Update
from telegram.ext import ContextTypes

from bot.enums import Command

from .help import handle_help
from .start import handle_start
from .tracking import handle_tracking_number


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if query.data == Command.TRACK:
        await handle_tracking_number(update, context)
    elif query.data == Command.HELP:
        await handle_help(update, context)
    elif query.data == Command.START:
        await handle_start(update, context)
    else:
        await query.answer("گزینه نامعتبر است.")
        return
