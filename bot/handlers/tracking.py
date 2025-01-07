from telegram import Message, Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.keyboards.markups import keyboard_markup_back
from bot.utils.text import (
    error_msg,
    format_tracking_record,
    normalize_text,
    warning_msg,
)
from bot.utils.tracking import track_shipment, validate_tracking_number

from .start import handle_start

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

        await update.message.reply_text("در حال رهگیری...", quote=True)

        try:
            tracking_records = await track_shipment(tracking_number, timeout=15000, normalizer=normalize_text)
        except Exception:
            await update.message.reply_text(error_msg("عملیات با خطا مواجه شد."))
            await handle_start(update, context)
            _end_conversation(context)
            raise

        if tracking_records:
            reply_text = "\n\n".join(
                [
                    f"شماره رهگیری: *{tracking_number}*",
                ]
                + [format_tracking_record(record) for record in tracking_records]
            )
            await update.message.reply_text(reply_text, parse_mode="markdown")
        else:
            await update.message.reply_text(warning_msg("نتیجه ای یافت نشد."))

        await handle_start(update, context)
        return _end_conversation(context)
