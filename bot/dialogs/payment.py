import hashlib
import json
from datetime import datetime, timezone

from aiogram.types import LabeledPrice, Message, PreCheckoutQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const

from bot.config import PRODUCTS, Settings
from bot.dialogs.states import DeliverySG, MainMenuSG, PaymentSG
from bot.models import Order
from bot.services.notification_service import NotificationService
from bot.services.order_service import OrderService

order_service: OrderService | None = None
notification_service: NotificationService | None = None
payment_settings: Settings | None = None
pending_orders: dict[str, Order] = {}


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
        order = _build_order(manager, "Оплачен через Telegram Payments")
        payload = _build_order_payload(manager, order)
        pending_orders[payload] = order

        await manager.event.bot.send_invoice(
            chat_id=manager.event.from_user.id,
            title=product["name"],
            description=product["description"],
            payload=payload,
            provider_token=payment_settings.payment_provider_token,
            currency="RUB",
            prices=[
                LabeledPrice(label=product["name"], amount=product["price_new"] * 100),
            ],
            need_email=True,
            send_email_to_provider=True,
            provider_data=json.dumps(
                payment_settings.yookassa_receipt.build_provider_data(
                    product["name"],
                    product["price_new"],
                ),
                ensure_ascii=False,
            ),
        )
    except Exception:
        await manager.event.answer(
            "Не удалось сформировать счет на оплату. Проверьте данные и попробуйте снова."
        )
        return


async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


async def successful_payment_handler(message: Message, dialog_manager: DialogManager):
    if order_service is None or notification_service is None:
        await message.answer(
            "Оплата получена, но сервис заказа недоступен. Мы свяжемся с вами для подтверждения."
        )
        return

    if message.successful_payment is None:
        return

    payload = message.successful_payment.invoice_payload
    order = pending_orders.pop(payload, None)
    if order is None:
        await message.answer(
            "Оплата получена, но заказ не найден. Мы свяжемся с вами для подтверждения."
        )
        return

    try:
        order_service.create_order(order)
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
        Const(
            "Поздравляю 💖✨с покупкой, скоро твой браслет отправиться к тебе! Как только заказ будет зарегистрирован, тебе придет трек номер. Хорошего тебе дня🙏🏻"
        ),
        Button(Const("Назад"), id="back_start", on_click=to_start),
        state=PaymentSG.done,
    ),
)
