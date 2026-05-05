import sqlite3
from pathlib import Path


class SQLiteDatabase:
    """SQLite БД для хранения заказов."""

    def __init__(self, db_path: str = "/app/data/orders.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    product_name TEXT NOT NULL,
                    product_price_old INTEGER,
                    product_price_new INTEGER NOT NULL,
                    delivery_type TEXT NOT NULL,
                    delivery_data TEXT NOT NULL,
                    payment_type TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_order(self, order_data: dict) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO orders (
                    user_id,
                    username,
                    first_name,
                    product_name,
                    product_price_old,
                    product_price_new,
                    delivery_type,
                    delivery_data,
                    payment_type,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_data["user_id"],
                    order_data.get("username"),
                    order_data.get("first_name"),
                    order_data["product_name"],
                    order_data.get("product_price_old"),
                    order_data["product_price_new"],
                    order_data["delivery_type"],
                    order_data["delivery_data"],
                    order_data["payment_type"],
                    order_data["created_at"],
                ),
            )
            conn.commit()
