import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, setup_dialogs

from bot.config import TEXTS, load_settings
from bot.database import SQLiteDatabase
from bot.dialogs import (
    catalog_dialog,
    delivery_dialog,
    main_menu_dialog,
    payment_dialog,
    product_dialog,
)
from bot.dialogs.payment import set_notification_service, set_order_service
from bot.dialogs.states import MainMenuSG
from bot.services.notification_service import NotificationService
from bot.services.order_service import OrderService

async def start_handler(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(MainMenuSG.start)


async def fallback_handler(message: Message):
    await message.answer(TEXTS["unknown"])


async def main():
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()
    router = Router()

    db = SQLiteDatabase()
    order_service = OrderService(db)
    notification_service = NotificationService(settings.admin_chat_id)
    set_order_service(order_service)
    set_notification_service(notification_service)

    router.message.register(start_handler, CommandStart())
    router.message.register(fallback_handler, MainMenuSG.start)

    dp.include_router(router)
    dp.include_router(main_menu_dialog)
    dp.include_router(catalog_dialog)
    dp.include_router(product_dialog)
    dp.include_router(delivery_dialog)
    dp.include_router(payment_dialog)

    setup_dialogs(dp)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
