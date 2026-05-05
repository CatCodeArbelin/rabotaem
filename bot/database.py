import sqlite3
from pathlib import Path


class SQLiteDatabase:
    """SQLite БД для хранения заказов."""

    def __init__(self, db_path: str = "/app/data/orders.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

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
                    created_at TEXT NOT NULL,
                    payment_status TEXT NOT NULL DEFAULT 'pending_payment',
                    invoice_payload TEXT,
                    telegram_payment_charge_id TEXT,
                    provider_payment_charge_id TEXT,
                    payment_total_amount INTEGER,
                    payment_currency TEXT
                )
                """
            )
            self._ensure_order_columns(conn)
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_invoice_payload
                ON orders(invoice_payload)
                WHERE invoice_payload IS NOT NULL
                """
            )
            conn.commit()

    @staticmethod
    def _ensure_order_columns(conn: sqlite3.Connection) -> None:
        existing_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(orders)").fetchall()
        }
        migrations = {
            "payment_status": "TEXT NOT NULL DEFAULT 'pending_payment'",
            "invoice_payload": "TEXT",
            "telegram_payment_charge_id": "TEXT",
            "provider_payment_charge_id": "TEXT",
            "payment_total_amount": "INTEGER",
            "payment_currency": "TEXT",
        }

        for column_name, column_definition in migrations.items():
            if column_name not in existing_columns:
                conn.execute(
                    f"ALTER TABLE orders ADD COLUMN {column_name} {column_definition}"
                )

        if "status" in existing_columns and "payment_status" not in existing_columns:
            conn.execute(
                """
                UPDATE orders
                SET payment_status = COALESCE(status, payment_status)
                """
            )

    def save_order(self, order_data: dict) -> None:
        with self._get_connection() as conn:
            invoice_payload = order_data.get("invoice_payload")
            payment_status = order_data.get(
                "payment_status", order_data.get("status", "pending_payment")
            )
            if invoice_payload:
                existing_order = conn.execute(
                    "SELECT id FROM orders WHERE invoice_payload = ?",
                    (invoice_payload,),
                ).fetchone()
                if existing_order is not None:
                    conn.execute(
                        """
                        UPDATE orders SET
                            user_id = ?,
                            username = ?,
                            first_name = ?,
                            product_name = ?,
                            product_price_old = ?,
                            product_price_new = ?,
                            delivery_type = ?,
                            delivery_data = ?,
                            payment_type = ?,
                            created_at = ?,
                            payment_status = ?,
                            invoice_payload = ?,
                            telegram_payment_charge_id = ?,
                            provider_payment_charge_id = ?,
                            payment_total_amount = ?,
                            payment_currency = ?
                        WHERE invoice_payload = ?
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
                            payment_status,
                            invoice_payload,
                            order_data.get("telegram_payment_charge_id"),
                            order_data.get("provider_payment_charge_id"),
                            order_data.get("payment_total_amount"),
                            order_data.get("payment_currency"),
                            invoice_payload,
                        ),
                    )
                    conn.commit()
                    return

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
                    created_at,
                    payment_status,
                    invoice_payload,
                    telegram_payment_charge_id,
                    provider_payment_charge_id,
                    payment_total_amount,
                    payment_currency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    payment_status,
                    invoice_payload,
                    order_data.get("telegram_payment_charge_id"),
                    order_data.get("provider_payment_charge_id"),
                    order_data.get("payment_total_amount"),
                    order_data.get("payment_currency"),
                ),
            )
            conn.commit()

    def get_order_by_invoice_payload(self, invoice_payload: str) -> dict | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM orders WHERE invoice_payload = ?",
                (invoice_payload,),
            ).fetchone()

        return dict(row) if row is not None else None
