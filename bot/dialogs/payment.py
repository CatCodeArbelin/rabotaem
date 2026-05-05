import hashlib
import json
import logging
from datetime import datetime, timezone

from aiogram.types import LabeledPrice, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const

from bot.config import PRODUCTS, Settings, TEXTS
from bot.dialogs.states import DeliverySG, MainMenuSG, PaymentSG
from bot.models import Order, PaymentDetails
from bot.services.notification_service import NotificationService
from bot.services.order_service import OrderService

order_service: OrderService | None = None
notification_service: NotificationService | None = None
payment_settings: Settings | None = None
pending_orders: dict[str, Order] = {}
logger = logging.getLogger(__name__)


def set_order_service(service: OrderService) -> None:
    global order_service
    order_service = service


def set_notification_service(service: NotificationService) -> None:
    global notification_service
    notification_service = service


def set_payment_settings(settings: Settings) -> None:
    global payment_settings
    payment_settings = settings


def _get_product(product_id: str | None) -> dict:
    product = next((p for p in PRODUCTS["bracelets"] if p["id"] == product_id), None)
    if product is None:
        raise ValueError("Не удалось определить выбранный товар")

    return product


def _build_order(manager: DialogManager, payment_type: str) -> Order:
    product = _get_product(manager.start_data.get("product_id"))

    event = manager.event
    if event is None or getattr(event, "from_user", None) is None:
        raise ValueError("Не удалось определить данные пользователя")

    user = event.from_user
    delivery_type = manager.start_data.get("delivery_method")
    delivery_data = manager.start_data.get("delivery_data")
    if not delivery_type or not delivery_data:
        raise ValueError("Не заполнены данные доставки")

    return Order(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        product_name=product["name"],
        product_price_old=product["price_old"],
        product_price_new=product["price_new"],
        delivery_type=delivery_type,
        delivery_data=delivery_data,
        payment_type=payment_type,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def _build_order_payload(manager: DialogManager, order: Order) -> str:
    product_id = manager.start_data.get("product_id")
    payload_data = {
        "delivery_data": order.delivery_data,
        "delivery_type": order.delivery_type,
        "product_id": product_id,
        "user_id": order.user_id,
    }
    digest = hashlib.sha256(
        json.dumps(payload_data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]

    return f"order:{order.user_id}:{product_id}:{digest}"


async def process_order_confirm(_, __, manager: DialogManager):
    if payment_settings is None:
        await manager.event.answer("Ошибка настроек оплаты. Попробуйте позже.")
        return

    try:
        product = _get_product(manager.start_data.get("product_id"))
        order = _build_order(manager, "Telegram/YooKassa")
        payload = _build_order_payload(manager, order)
        order.invoice_payload = payload
        order.payment_status = "pending_payment"
        if order_service is not None:
            order_service.create_order(order)
        pending_orders[payload] = order

        invoice_kwargs = {
            "chat_id": manager.event.from_user.id,
            "title": product["name"],
            "description": product["description"],
            "payload": payload,
            "provider_token": payment_settings.payment_provider_token,
            "currency": "RUB",
            "prices": [
                LabeledPrice(label=product["name"], amount=product["price_new"] * 100),
            ],
            # Данные доставки уже собираются вручную в delivery_dialog, поэтому
            # Telegram shipping_query и адрес доставки в invoice не запрашиваем.
            "need_shipping_address": False,
            "need_email": True,
            "send_email_to_provider": True,
        }
        if payment_settings.yookassa_send_receipt:
            invoice_kwargs["provider_data"] = json.dumps(
                payment_settings.yookassa_receipt.build_provider_data(
                    product["name"],
                    product["price_new"],
                ),
                ensure_ascii=False,
            )

        await manager.event.bot.send_invoice(**invoice_kwargs)
    except Exception as exc:
        logger.exception("Failed to send Telegram invoice")
        await manager.event.answer(
            "Не удалось сформировать счет на оплату. Проверьте данные и попробуйте снова."
        )
        return


def has_pending_order_payload(payload: str | None) -> bool:
    if not payload:
        return False
    if payload in pending_orders:
        return True
    if order_service is None:
        return False

    order = order_service.get_order_by_invoice_payload(payload)
    return order is not None and order.payment_status == "pending_payment"


async def process_successful_payment(
    message: Message,
    dialog_manager: DialogManager,
    payment_details: PaymentDetails,
):
    if order_service is None:
        await message.answer(
            "Оплата получена, но сервис заказа недоступен. Мы свяжемся с вами для подтверждения."
        )
        return

    payload = payment_details.invoice_payload
    order = pending_orders.pop(payload, None)
    if order is None:
        order = order_service.get_order_by_invoice_payload(payload)

    if order is None:
        await message.answer(
            "Оплата получена, но заказ не найден. Мы свяжемся с вами для подтверждения."
        )
        return

    try:
        order_service.mark_order_paid(order, payment_details)
        if notification_service is not None:
            await notification_service.send_order_notification(message.bot, order)
    except Exception:
        pending_orders[payload] = order
        await message.answer(
            "Оплата получена, но заказ пока не удалось сохранить. Попробуйте написать нам для подтверждения."
        )
        return

    await dialog_manager.switch_to(PaymentSG.done)


async def back_to_delivery_input(_, __, manager: DialogManager):
    await manager.start(
        DeliverySG.full_name_input,
        data={"product_id": manager.start_data.get("product_id")},
    )


async def to_start(_, __, manager: DialogManager):
    await manager.start(MainMenuSG.start)


payment_dialog = Dialog(
    Window(
        Const("Проверьте данные и подтвердите заказ:"),
        Button(
            Const("Оформить заказ"), id="confirm_order", on_click=process_order_confirm
        ),
        Button(
            Const("Назад"), id="back_delivery_input", on_click=back_to_delivery_input
        ),
        state=PaymentSG.payment,
    ),
    Window(
        Const(TEXTS["order_done"]),
        Button(Const("Назад"), id="back_start", on_click=to_start),
        state=PaymentSG.done,
    ),
)
