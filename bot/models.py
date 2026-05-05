from dataclasses import dataclass


@dataclass
class Product:
    """Модель товара для отображения в каталоге."""

    id: str
    name: str
    price: int
    description: str


@dataclass
class OrderDraft:
    """Черновик заказа, который собирается по шагам диалога."""

    product_id: str
    delivery_method: str | None = None
    delivery_data: str | None = None
    payment_method: str | None = None


@dataclass
class PaymentDetails:
    """Данные успешного платежа Telegram Payments."""

    provider_payment_charge_id: str
    telegram_payment_charge_id: str
    invoice_payload: str
    total_amount: int
    currency: str


@dataclass
class Order:
    """Полная модель заказа для передачи в сервис сохранения."""

    user_id: int
    username: str | None
    first_name: str | None
    product_name: str
    product_price_old: int | None
    product_price_new: int
    delivery_type: str
    delivery_data: str
    payment_type: str
    created_at: str
    status: str = "pending_payment"
    provider_payment_charge_id: str | None = None
    telegram_payment_charge_id: str | None = None
    invoice_payload: str | None = None
    payment_total_amount: int | None = None
    payment_currency: str | None = None
