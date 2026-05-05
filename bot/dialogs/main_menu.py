from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format

from bot.config import TEXTS
from bot.dialogs.states import CatalogSG, MainMenuSG


async def on_bracelets_click(_, __, manager: DialogManager):
    # Переходим в каталог браслетов.
    await manager.start(CatalogSG.catalog)


async def on_chokers_click(_, __, manager: DialogManager):
    # Переходим на экран-заглушку чокеров.
    await manager.switch_to(MainMenuSG.chokers_stub)


async def on_back_from_stub(_, __, manager: DialogManager):
    # Возвращаемся в главное меню из заглушки.
    await manager.switch_to(MainMenuSG.start)


async def start_getter(dialog_manager: DialogManager, **kwargs):
    event = dialog_manager.event
    first_name = getattr(getattr(event, "from_user", None), "first_name", None) or "Леди"
    return {"first_name": first_name}


main_menu_dialog = Dialog(
    Window(
        Format(TEXTS["start"]),
        StaticMedia(path="bot/dialogs/Ava.jpg", type="photo"),
        Button(Const("Браслеты ✨"), id="bracelets", on_click=on_bracelets_click),
        state=MainMenuSG.start,
        getter=start_getter,
    ),
    Window(
        Const("Чокеры Скоро Появятся ✨\nПока Что Доступны Только Браслеты 💖"),
        Button(Const("Назад"), id="back_stub", on_click=on_back_from_stub),
        state=MainMenuSG.chokers_stub,
    ),
)
