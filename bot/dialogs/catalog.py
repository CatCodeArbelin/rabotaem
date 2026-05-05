from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const

from bot.config import PRODUCTS, TEXTS
from bot.dialogs.states import CatalogSG, MainMenuSG, ProductSG


def _product_name(idx: int) -> str:
    return PRODUCTS["bracelets"][idx]["name"]


async def open_product_0(_, __, manager: DialogManager):
    await manager.start(ProductSG.product, data={"product_id": PRODUCTS["bracelets"][0]["id"]})


async def open_product_1(_, __, manager: DialogManager):
    await manager.start(ProductSG.product, data={"product_id": PRODUCTS["bracelets"][1]["id"]})


async def open_product_2(_, __, manager: DialogManager):
    await manager.start(ProductSG.product, data={"product_id": PRODUCTS["bracelets"][2]["id"]})


async def back_to_main(_, __, manager: DialogManager):
    await manager.start(MainMenuSG.start)


catalog_dialog = Dialog(
    Window(
        Const(TEXTS["catalog_title"]),
        Button(Const(_product_name(0)), id="p0", on_click=open_product_0),
        Button(Const(_product_name(1)), id="p1", on_click=open_product_1),
        Button(Const(_product_name(2)), id="p2", on_click=open_product_2),
        Button(Const("Назад"), id="back_main", on_click=back_to_main),
        state=CatalogSG.catalog,
    )
)
