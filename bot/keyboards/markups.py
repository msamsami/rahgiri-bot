from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.enums import Command

keyboard_markup_start = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("رهگیری مرسوله", callback_data=Command.TRACK)],
        [InlineKeyboardButton("راهنما", callback_data=Command.HELP)],
    ]
)

keyboard_markup_back = InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت", callback_data=Command.START)]])
