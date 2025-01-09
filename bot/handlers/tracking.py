from typing import Optional

from telegram import Message, Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.config import settings
from bot.enums import Command
from bot.keyboards.markups import keyboard_markup_back
from bot.models import TrackingRecord
from bot.utils.exceptions import TrackingError
from bot.utils.text import (
    error_msg,
    format_tracking_record,
    normalize_text,
    warning_msg,
)
from bot.utils.tracking import track_parcel, validate_tracking_number

from .start import handle_start

__all__ = ("handle_tracking_number", "handle_tracking_process", "tracking_conversation_handler")


START_TRACKING = 0
IS_TRACKING_FLAG = "is_tracking"
LAST_MESSAGE_ID_KEY = "last_message_id"


async def _delete_last_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data is not None and (last_message_id := context.user_data.get(LAST_MESSAGE_ID_KEY)):
        if update.effective_chat:
            chat_id = update.effective_chat.id
        elif update.message:
            chat_id = update.message.chat_id
        else:
            return
        await context.bot.delete_message(chat_id=chat_id, message_id=last_message_id)


def _end_conversation(context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data is not None:
        context.user_data.clear()
    return ConversationHandler.END


async def handle_tracking_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handler for tracking number input.
    """
    msg_text = "شماره رهگیری مرسوله را وارد کنید."

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = await query.edit_message_text(msg_text, reply_markup=keyboard_markup_back)
    elif update.message:
        message = await update.message.reply_text(msg_text, reply_markup=keyboard_markup_back)
    else:
        return _end_conversation(context)

    if context.user_data is not None:
        context.user_data[IS_TRACKING_FLAG] = True
        if isinstance(message, Message):
            context.user_data[LAST_MESSAGE_ID_KEY] = message.message_id

    return START_TRACKING


async def handle_tracking_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handler for parcel tracking process.
    """
    if not update.message or not context.user_data or not context.user_data.get(IS_TRACKING_FLAG):
        return _end_conversation(context)

    tracking_number = str(update.message.text).strip()

    if not validate_tracking_number(tracking_number):
        await update.message.reply_text(error_msg("شماره رهگیری مرسوله معتبر نیست."))
        await _delete_last_message(update, context)
        await handle_tracking_number(update, context)
        return START_TRACKING

    else:
        context.user_data.pop(IS_TRACKING_FLAG, None)
        await _delete_last_message(update, context)
        await update.message.reply_text("🔄 در حال رهگیری...", quote=True)

        tracking_records: Optional[list[TrackingRecord]] = None
        try:
            tracking_records = await track_parcel(tracking_number, timeout=settings.tracking_timeout, normalizer=normalize_text)
        except TrackingError as e:
            await update.message.reply_text(error_msg(str(e)))
        except Exception:
            await update.message.reply_text(error_msg("عملیات با خطا مواجه شد. لطفا دقایقی دیگر مجددا تلاش کنید."))
            await handle_start(update, context)
            _end_conversation(context)
            raise

        if tracking_records is not None:
            if tracking_records:
                reply_text = "\n\n".join(
                    [
                        f"✅ شماره رهگیری: *{tracking_number}*",
                    ]
                    + [format_tracking_record(record) for record in tracking_records]
                )
                await update.message.reply_text(reply_text, parse_mode="markdown")
            else:
                await update.message.reply_text(warning_msg("نتیجه ای یافت نشد!"))

        await handle_start(update, context)
        return _end_conversation(context)


tracking_conversation_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(handle_tracking_number, pattern=Command.TRACK),
    ],
    states={
        START_TRACKING: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tracking_process),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(handle_start, pattern=Command.START),
    ],
    allow_reentry=True,
)
