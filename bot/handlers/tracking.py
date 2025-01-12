from typing import Optional

from playwright.async_api import ProxySettings
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
from bot.keyboards.markups import (
    OUTPUT_TYPE_CALLBACK_MAP,
    keyboard_markup_back,
    keyboard_markup_tracking_output_type,
)
from bot.models import TrackingRecord
from bot.utils.exceptions import TrackingError
from bot.utils.text import (
    error_msg,
    format_tracking_record,
    normalize_text,
    warning_msg,
)
from bot.utils.tracking import ParcelTracker, validate_tracking_number

from .start import REDIRECT_FROM_TRACKING_KEY, handle_start

__all__ = ("tracking_conversation_handler",)


WAITING_FOR_TRACKING_NUMBER = 0
WAITING_FOR_RESULT_TYPE = 1
IS_TRACKING_FLAG_KEY = "is_tracking"
LAST_MESSAGE_ID_KEY = "last_message_id"


async def _remove_keyboard_markup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data is not None and (last_message_id := context.user_data.get(LAST_MESSAGE_ID_KEY)):
        if update.effective_chat:
            chat_id = update.effective_chat.id
        elif update.message:
            chat_id = update.message.chat_id
        else:
            return
        await context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=last_message_id, reply_markup=None)


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

    if context.user_data is not None and isinstance(message, Message):
        context.user_data[LAST_MESSAGE_ID_KEY] = message.message_id

    return WAITING_FOR_TRACKING_NUMBER


async def handle_tracking_result_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handler for selecting the type of the tracking result.
    """
    if not update.message or not context.user_data:
        return _end_conversation(context)

    await _remove_keyboard_markup(update, context)

    tracking_number = str(update.message.text).strip()
    if not validate_tracking_number(tracking_number):
        await update.message.reply_text(error_msg("شماره رهگیری مرسوله معتبر نیست."))
        await handle_tracking_number(update, context)
        return WAITING_FOR_TRACKING_NUMBER

    context.user_data["tracking_number"] = tracking_number

    msg_text = "نوع نمایش نتیجه رهگیری را انتخاب کنید."
    if update.message:
        message = await update.message.reply_text(msg_text, reply_markup=keyboard_markup_tracking_output_type)
    else:
        return _end_conversation(context)

    context.user_data[IS_TRACKING_FLAG_KEY] = True
    if isinstance(message, Message):
        context.user_data[LAST_MESSAGE_ID_KEY] = message.message_id

    return WAITING_FOR_RESULT_TYPE


async def handle_tracking_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handler for parcel tracking process.
    """
    query = update.callback_query
    if not query or not context.user_data or not context.user_data.get(IS_TRACKING_FLAG_KEY):
        return _end_conversation(context)

    await query.answer()

    if not query.message or not query.data:
        return _end_conversation(context)

    result_type = query.data
    tracking_number = str(context.user_data.get("tracking_number")).strip()

    context.user_data.pop(IS_TRACKING_FLAG_KEY, None)
    await _remove_keyboard_markup(update, context)
    result_type_fa = OUTPUT_TYPE_CALLBACK_MAP.get(result_type, "تصویر")
    await context.bot.send_message(
        chat_id=query.message.chat.id,
        text="\n\n".join(["🔄 در حال رهگیری...", f"(نوع نمایش: *{result_type_fa}*)"]),
        parse_mode="markdown",
    )

    tracking_result: Optional[list[TrackingRecord] | bytes] = None
    try:
        proxy = None
        if settings.proxy_url:
            proxy = ProxySettings(server=settings.proxy_url)

        return_type = result_type if result_type in ("text", "image") else "image"

        tracker = ParcelTracker(normalizer=normalize_text, proxy=proxy)
        if return_type == "image":
            tracking_result = await tracker.track_as_image(tracking_number, timeout=settings.tracking_timeout)
        else:
            tracking_result = await tracker.track_as_text(tracking_number, timeout=settings.tracking_timeout)
    except TrackingError as e:
        await context.bot.send_message(chat_id=query.message.chat.id, text=error_msg(str(e)))
    except Exception:
        await context.bot.send_message(
            chat_id=query.message.chat.id, text=error_msg("عملیات با خطا مواجه شد. لطفا دقایقی دیگر مجددا تلاش کنید.")
        )
        context.user_data[REDIRECT_FROM_TRACKING_KEY] = True
        await handle_start(update, context)
        _end_conversation(context)
        raise

    if tracking_result is not None:
        if isinstance(tracking_result, bytes):
            await context.bot.send_photo(
                chat_id=query.message.chat.id,
                photo=tracking_result,
                caption=f"✅ شماره رهگیری: *{tracking_number}*",
                parse_mode="markdown",
            )
        else:
            if tracking_result:
                reply_text = "\n\n".join(
                    [
                        f"✅ شماره رهگیری: *{tracking_number}*",
                    ]
                    + [format_tracking_record(record) for record in tracking_result]
                )
                await context.bot.send_message(chat_id=query.message.chat.id, text=reply_text, parse_mode="markdown")
            else:
                await context.bot.send_message(chat_id=query.message.chat.id, text=warning_msg("نتیجه ای یافت نشد!"))

    context.user_data[REDIRECT_FROM_TRACKING_KEY] = True
    await handle_start(update, context)
    return _end_conversation(context)


tracking_conversation_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(handle_tracking_number, pattern=Command.TRACK),
    ],
    states={
        WAITING_FOR_TRACKING_NUMBER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tracking_result_type),
        ],
        WAITING_FOR_RESULT_TYPE: [
            CallbackQueryHandler(
                handle_tracking_process, pattern=f"^(?:{Command.TRACK_OUTPUT_TEXT.value}|{Command.TRACK_OUTPUT_IMAGE.value})$"
            ),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(handle_start, pattern=Command.START),
    ],
    allow_reentry=True,
)
