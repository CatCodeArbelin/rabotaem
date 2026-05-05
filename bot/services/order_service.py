from dataclasses import asdict, fields

from bot.database import SQLiteDatabase
from bot.models import Order, PaymentDetails


class OrderService:
    """Сервис для сохранения заказов из диалога."""

    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def create_order(self, order: Order) -> None:
        """Создает заказ и передает его в БД."""
        self.db.save_order(asdict(order))

    def get_order_by_invoice_payload(self, invoice_payload: str) -> Order | None:
        """Восстанавливает заказ по payload счета Telegram Payments."""
        order_data = self.db.get_order_by_invoice_payload(invoice_payload)
        if order_data is None:
            return None

        order_fields = {field.name for field in fields(Order)}
        return Order(
            **{key: value for key, value in order_data.items() if key in order_fields}
        )

    def mark_order_paid(self, order: Order, payment_details: PaymentDetails) -> None:
        """Обновляет заказ данными успешного платежа."""
        order.status = "paid"
        order.payment_type = "Telegram/YooKassa"
        order.provider_payment_charge_id = payment_details.provider_payment_charge_id
        order.telegram_payment_charge_id = payment_details.telegram_payment_charge_id
        order.invoice_payload = payment_details.invoice_payload
        order.payment_total_amount = payment_details.total_amount
        order.payment_currency = payment_details.currency
        self.create_order(order)
