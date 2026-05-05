import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_chat_id: int | None


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


def load_settings() -> Settings:
    """Загружает настройки из переменных окружения."""
    bot_token = os.getenv("BOT_TOKEN", "")
    admin_chat_id_raw = os.getenv("ADMIN_CHAT_ID", "")

    if not bot_token:
        raise ValueError("Переменная окружения BOT_TOKEN не задана")
    admin_chat_id: int | None = None
    if admin_chat_id_raw:
        try:
            admin_chat_id = int(admin_chat_id_raw)
        except ValueError as exc:
            raise ValueError("ADMIN_CHAT_ID должен быть целым числом") from exc

    return Settings(bot_token=bot_token, admin_chat_id=admin_chat_id)
