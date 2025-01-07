import logging
from functools import partial

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.enums import Command
from bot.handlers import button_handler
from bot.handlers.error import handle_error
from bot.handlers.help import handle_help
from bot.handlers.start import handle_start
from bot.handlers.tracking import handle_tracking_process

from .config import settings

__version__ = "0.1.0"


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    application = ApplicationBuilder().token(settings.telegram_token).connect_timeout(15).build()

    application.add_handler(CommandHandler(Command.START, handle_start))
    application.add_handler(CommandHandler(Command.HELP, handle_help))
    application.add_handler(MessageHandler(filters.Regex("^(help|راهنما)$"), handle_help))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tracking_process))
    application.add_error_handler(partial(handle_error, chat_id=settings.developer_chat_id))

    application.run_polling()


if __name__ == "__main__":
    main()
