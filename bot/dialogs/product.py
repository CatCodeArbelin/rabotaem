from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Format

from bot.config import PRODUCTS, TEXTS
from bot.dialogs.states import CatalogSG, DeliverySG, ProductSG


def _format_price(value: int) -> str:
    return f"{value:,}".replace(",", " ")


async def product_getter(dialog_manager: DialogManager, **_):
    product_id = dialog_manager.start_data.get("product_id")
    product = next(p for p in PRODUCTS["bracelets"] if p["id"] == product_id)
    return {
        "photo_1": product["photos"][0],
        "photo_2": product["photos"][1],
        "card": TEXTS["product_card"].format(
            name=product["name"],
            price_old=_format_price(product["price_old"]),
            price_new=_format_price(product["price_new"]),
            description=product["description"],
        ),
    }


async def to_delivery(_, __, manager: DialogManager):
    await manager.start(DeliverySG.delivery, data={"product_id": manager.start_data.get("product_id")})


async def back_to_catalog(_, __, manager: DialogManager):
    await manager.start(CatalogSG.catalog)


async def show_photo_2(_, __, manager: DialogManager):
    await manager.switch_to(ProductSG.product_photo_2)


async def show_photo_1(_, __, manager: DialogManager):
    await manager.switch_to(ProductSG.product)


product_dialog = Dialog(
    Window(
        Format("{card}\n\nФото 1/2"),
        StaticMedia(path=Format("{photo_1}"), type="photo"),
        Button(Format("Следующее Фото ▶️"), id="next_photo", on_click=show_photo_2),
        Button(Format("Заказать"), id="order", on_click=to_delivery),
        Button(Format("Назад"), id="back_catalog", on_click=back_to_catalog),
        state=ProductSG.product,
        getter=product_getter,
    ),
    Window(
        Format("{card}\n\nФото 2/2"),
        StaticMedia(path=Format("{photo_2}"), type="photo"),
        Button(Format("◀️ Предыдущее Фото"), id="prev_photo", on_click=show_photo_1),
        Button(Format("Заказать"), id="order_2", on_click=to_delivery),
        Button(Format("Назад"), id="back_catalog_2", on_click=back_to_catalog),
        state=ProductSG.product_photo_2,
        getter=product_getter,
    ),
)
