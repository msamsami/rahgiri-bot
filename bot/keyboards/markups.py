from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.enums import Command

OUTPUT_TYPE_CALLBACK_MAP: dict[str | Command, str] = {
    Command.TRACK_OUTPUT_TEXT: "متن",
    Command.TRACK_OUTPUT_IMAGE: "عکس",
}


keyboard_markup_start = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("رهگیری مرسوله", callback_data=Command.TRACK)],
        [InlineKeyboardButton("راهنما", callback_data=Command.HELP)],
    ]
)


keyboard_markup_tracking_output_type = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text, callback_data=callback_data) for callback_data, text in OUTPUT_TYPE_CALLBACK_MAP.items()],
        [InlineKeyboardButton("بازگشت", callback_data=Command.START)],
    ]
)

keyboard_markup_back = InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data=Command.START)]])
