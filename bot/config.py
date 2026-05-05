import logging
import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReceiptSettings:
    """Настройки фискального чека для provider_data.receipt ЮKassa."""

    customer_email: str | None
    customer_phone: str | None
    tax_system_code: int | None
    vat_code: int
    payment_subject: str
    payment_mode: str

    def build_provider_data(self, title: str, amount: int) -> dict[str, Any]:
        """Формирует provider_data платежа Telegram через ЮKassa."""
        return {"receipt": self.build_provider_receipt(title, amount)}

    def build_provider_receipt(self, title: str, amount: int) -> dict[str, Any]:
        """Формирует receipt для provider_data платежа Telegram через ЮKassa."""
        customer: dict[str, str] = {}
        if self.customer_email:
            customer["email"] = self.customer_email
        if self.customer_phone:
            customer["phone"] = self.customer_phone

        receipt: dict[str, Any] = {
            "items": [
                {
                    "description": title,
                    "quantity": "1.00",
                    "amount": {
                        "value": f"{amount:.2f}",
                        "currency": "RUB",
                    },
                    "vat_code": self.vat_code,
                    "payment_subject": self.payment_subject,
                    "payment_mode": self.payment_mode,
                }
            ]
        }
        if customer:
            receipt["customer"] = customer
        if self.tax_system_code is not None:
            receipt["tax_system_code"] = self.tax_system_code

        return receipt


@dataclass(frozen=True)
class Settings:
    bot_token: str
    payment_provider_token: str
    admin_chat_id: int | None
    yookassa_receipt: ReceiptSettings


TEXTS = {
    "start": (
        "Милая Леди, здесь ты можешь выбрать украшения ✨\n\n"
        "{first_name}, выбери, что тебя интересует:"
    ),
    "main_menu": "Главное меню:",
    "catalog_title": "Выбери Браслет ✨",
    "chokers_stub": (
        "Скоро здесь появятся чокеры ✨\n"
        "Следите за обновлениями — а пока выберите браслеты в каталоге 💖"
    ),
    "product_card": (
        "{name}\n"
        "Цена: <s>{price_old}₽</s>\n"
        "✨ Цена Сегодня: {price_new}₽✅\n\n"
        "{description}"
    ),
    "choose_delivery": "Выбери Способ Доставки:",
    "choose_payment": "Выбери Способ Оплаты:",
    "order_done": (
        "Спасибо За Заказ 💖\n\n"
        "После того как заказ отправится, я пришлю трек-номер для отслеживания.\n\n"
        "Хорошего Дня ✨"
    ),
    "unknown": (
        "Я Пока Не Понимаю Это Сообщение 🙏\n"
        "Используй Кнопки Ниже Или Введи Данные Доставки На Нужном Шаге."
    ),
}

DELIVERY_CHOICE_TEXT = "Выбери способ доставки для товара: {product_name}"
DELIVERY_POST_INPUT_TEXT = (
    "Отправь данные доставки одним сообщением.\n"
    "Например: ФИО, телефон, индекс, город, улица, дом, квартира"
)
DELIVERY_CDEK_INPUT_TEXT = (
    "Отправь данные доставки одним сообщением.\n"
    "Например: Ф.И.О., телефон, город, адрес ПВЗ Сдэк"
)


PRODUCTS = {
    "bracelets": [
        {
            "id": "b1",
            "name": "Браслет Мелисса",
            "price_old": 3500,
            "price_new": 2500,
            "photos": ["bot/dialogs/melissa1.jpg", "bot/dialogs/melissa2.jpg"],
            "description": (
                "Жемчуг 🐚 и голубика 🫐 — нежное сочетание с мягким сиянием.\n"
                "Тип замка: магнитный."
            ),
        },
        {
            "id": "b2",
            "name": "Браслет Сияние",
            "price_old": 2700,
            "price_new": 1700,
            "photos": ["bot/dialogs/siyanie1.jpg", "bot/dialogs/siyanie2.jpg"],
            "description": (
                "Алмазная крошка создает яркое мерцание и эффект сияния.\n"
                "Акцент тюльпана 🌷 добавляет романтичное настроение.\n"
                "Тип замка: классический."
            ),
        },
        {
            "id": "b3",
            "name": "Браслет Нежность",
            "price_old": 3500,
            "price_new": 2500,
            "photos": ["bot/dialogs/newsnost1.jpg", "bot/dialogs/newsnost2.jpg"],
            "description": (
                "Жемчуг и алмазная крошка вместе создают деликатное сияние.\n"
                "Тюльпан 🌷 делает браслет особенно нежным.\n"
                "Тип замка: магнитный."
            ),
        },
    ],
       "chokers": [],
}


def _get_payment_provider_token_mode(token: str) -> str:
    """Определяет режим provider token без раскрытия секрета."""
    normalized_token = token.upper()
    if ":TEST:" in normalized_token:
        return "test"
    if ":LIVE:" in normalized_token:
        return "live"
    return "unknown"


def _log_payment_provider_token_mode(token: str) -> None:
    mode = _get_payment_provider_token_mode(token)
    if mode == "test":
        logging.info("Приложение запущено с тестовым платежным provider token")
        return
    if mode == "live":
        logging.info("Приложение запущено с боевым платежным provider token")
        return

    logging.warning(
        "Не удалось определить режим платежного provider token: "
        "ожидается маркер TEST или LIVE в токене из BotFather"
    )


def _get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Переменная окружения {name} не задана")
    return value


def _get_optional_int_env(name: str) -> int | None:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return None
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} должен быть целым числом") from exc


def load_settings() -> Settings:
    """Загружает настройки из переменных окружения."""
    bot_token = _get_required_env("BOT_TOKEN")
    payment_provider_token = _get_required_env("PAYMENT_PROVIDER_TOKEN")
    _log_payment_provider_token_mode(payment_provider_token)
    admin_chat_id = _get_optional_int_env("ADMIN_CHAT_ID")

    yookassa_receipt = ReceiptSettings(
        customer_email=os.getenv("YOOKASSA_RECEIPT_EMAIL", "").strip() or None,
        customer_phone=os.getenv("YOOKASSA_RECEIPT_PHONE", "").strip() or None,
        tax_system_code=_get_optional_int_env("YOOKASSA_TAX_SYSTEM_CODE"),
        vat_code=_get_optional_int_env("YOOKASSA_VAT_CODE") or 1,
        payment_subject=os.getenv("YOOKASSA_PAYMENT_SUBJECT", "commodity").strip() or "commodity",
        payment_mode=os.getenv("YOOKASSA_PAYMENT_MODE", "full_payment").strip() or "full_payment",
    )

    return Settings(
        bot_token=bot_token,
        payment_provider_token=payment_provider_token,
        admin_chat_id=admin_chat_id,
        yookassa_receipt=yookassa_receipt,
    )
