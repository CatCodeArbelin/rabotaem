import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message, PreCheckoutQuery
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
from bot.dialogs.payment import (
    has_pending_order_payload,
    process_successful_payment,
    set_notification_service,
    set_order_service,
    set_payment_settings,
)
from bot.dialogs.states import MainMenuSG
from bot.models import PaymentDetails
from bot.services.notification_service import NotificationService
from bot.services.order_service import OrderService


async def start_handler(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(MainMenuSG.start)


async def fallback_handler(message: Message):
    await message.answer(TEXTS["unknown"])


async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    if has_pending_order_payload(pre_checkout_query.invoice_payload):
        await pre_checkout_query.answer(ok=True)
        return

    await pre_checkout_query.answer(
        ok=False,
        error_message="Не удалось проверить заказ",
    )


async def successful_payment_message_handler(
    message: Message,
    dialog_manager: DialogManager,
):
    if message.successful_payment is None:
        return

    successful_payment = message.successful_payment
    payment_details = PaymentDetails(
        provider_payment_charge_id=successful_payment.provider_payment_charge_id,
        telegram_payment_charge_id=successful_payment.telegram_payment_charge_id,
        invoice_payload=successful_payment.invoice_payload,
        total_amount=successful_payment.total_amount,
        currency=successful_payment.currency,
    )
    await process_successful_payment(message, dialog_manager, payment_details)


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
    set_payment_settings(settings)

    router.message.register(start_handler, CommandStart())
    router.pre_checkout_query.register(pre_checkout_handler)
    router.message.register(successful_payment_message_handler, F.successful_payment)
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
