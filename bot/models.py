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
