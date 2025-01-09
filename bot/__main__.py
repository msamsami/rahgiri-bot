import logging

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler

from bot.enums import Command
from bot.handlers import button_handler
from bot.handlers.error import handle_error
from bot.handlers.start import handle_start
from bot.handlers.tracking import tracking_conversation_handler

from .config import settings

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    application = ApplicationBuilder().token(settings.telegram_token).connect_timeout(15).build()

    application.add_handler(tracking_conversation_handler)
    application.add_handler(CommandHandler(Command.START, handle_start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_error_handler(handle_error)

    application.run_polling()


if __name__ == "__main__":
    main()
