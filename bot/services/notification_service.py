import logging

from aiogram import Bot

from bot.models import Order


class NotificationService:
    """Сервис уведомления администратора о новом заказе."""

    def __init__(self, admin_chat_id: int | None) -> None:
        self.admin_chat_id = admin_chat_id

    @staticmethod
    def format_order_message(order: Order) -> str:
        username = f"@{order.username}" if order.username else "—"
        first_name = order.first_name or "—"

        delivery_data = order.delivery_data or "—"
        delivery_data_formatted = "\n".join(
            f"  {line}" for line in str(delivery_data).splitlines()
        )

        return (
            "Новый заказ 💖\n\n"
            "Пользователь:\n"
            f"• Telegram ID: {order.user_id}\n"
            f"• Username: {username}\n"
            f"• Имя: {first_name}\n\n"
            "Товар:\n"
            f"• {order.product_name}\n"
            f"• Цена: {order.product_price_new}₽\n\n"
            "Доставка:\n"
            f"• Способ: {order.delivery_type}\n"
            "• Данные:\n"
            f"{delivery_data_formatted}\n\n"
            "Оплата:\n"
            f"• {order.payment_type}\n\n"
            "Дата:\n"
            f"• {order.created_at}"
        )

    async def send_order_notification(self, bot: Bot, order: Order) -> None:
        if self.admin_chat_id is None:
            return

        try:
            await bot.send_message(
                chat_id=self.admin_chat_id,
                text=self.format_order_message(order),
            )
        except Exception:
            logging.exception(
                "Не удалось отправить уведомление администратору (admin_chat_id=%s, order_user_id=%s)",
                self.admin_chat_id,
                order.user_id,
            )
