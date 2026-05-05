from dataclasses import asdict

from bot.database import SQLiteDatabase
from bot.models import Order


class OrderService:
    """Сервис для сохранения заказов из диалога."""

    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def create_order(self, order: Order) -> None:
        """Создает заказ и передает его в БД."""
        self.db.save_order(asdict(order))
