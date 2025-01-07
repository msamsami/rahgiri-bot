import html
import json
import logging
import traceback
from typing import Optional

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE, chat_id: Optional[int | str] = None) -> None:
    """
    Log the error and optionally send a telegram message to notify the developer.
    """
    logging.error("Exception while handling an update:", exc_info=context.error)

    if not context.error:
        return

    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "خطا: \n\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    if chat_id:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.HTML)
        except Exception as e:
            logging.error(f"Failed to send error message to developer chat: {e}")
