from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format

from bot.config import DELIVERY_CHOICE_TEXT, PRODUCTS
from bot.dialogs.states import DeliverySG, PaymentSG, ProductSG




async def on_full_name_input(message, _widget, manager: DialogManager):
    manager.dialog_data["full_name"] = (message.text or "").strip()
    await manager.switch_to(DeliverySG.full_name_confirm)


async def on_phone_input(message, _widget, manager: DialogManager):
    phone = (message.text or "").strip()
    if not phone or any(not (ch.isdigit() or ch == "+") for ch in phone):
        await message.answer("Телефон может содержать только цифры и символ +. Попробуйте еще раз.")
        return
    manager.dialog_data["phone"] = phone
    await manager.switch_to(DeliverySG.phone_confirm)


async def on_address_input(message, _widget, manager: DialogManager):
    manager.dialog_data["address"] = (message.text or "").strip()
    await manager.switch_to(DeliverySG.address_confirm)

async def set_post(_, __, manager: DialogManager):
    manager.dialog_data["delivery_method"] = "Почта"
    manager.dialog_data.update({"full_name": "", "phone": "", "address": ""})
    await manager.switch_to(DeliverySG.full_name_input)


async def set_cdek(_, __, manager: DialogManager):
    manager.dialog_data["delivery_method"] = "Сдэк"
    manager.dialog_data.update({"full_name": "", "phone": "", "address": ""})
    await manager.switch_to(DeliverySG.full_name_input)


async def back_to_product(_, __, manager: DialogManager):
    await manager.start(ProductSG.product, data={"product_id": manager.start_data.get("product_id")})


async def back_delivery(_, __, manager: DialogManager):
    await manager.switch_to(DeliverySG.delivery)


async def to_phone_input(_, __, manager: DialogManager):
    await manager.switch_to(DeliverySG.phone_input)


async def to_full_name_input(_, __, manager: DialogManager):
    await manager.switch_to(DeliverySG.full_name_input)


async def to_address_input(_, __, manager: DialogManager):
    await manager.switch_to(DeliverySG.address_input)


async def to_full_name_confirm(_, __, manager: DialogManager):
    await manager.switch_to(DeliverySG.full_name_confirm)

async def to_phone_confirm(_, __, manager: DialogManager):
    await manager.switch_to(DeliverySG.phone_confirm)


async def to_payment(_, __, manager: DialogManager):
    await manager.start(
        PaymentSG.payment,
        data={
            "product_id": manager.start_data.get("product_id"),
            "delivery_method": manager.dialog_data.get("delivery_method"),
            "delivery_data": (
                f"ФИО: {manager.dialog_data.get('full_name', '')}\n"
                f"Телефон: {manager.dialog_data.get('phone', '')}\n"
                f"Адрес: {manager.dialog_data.get('address', '')}"
            ),
        },
    )


async def confirm_full_name_yes(_, __, manager: DialogManager):
    await manager.switch_to(DeliverySG.phone_input)


async def confirm_full_name_no(_, __, manager: DialogManager):
    await manager.switch_to(DeliverySG.full_name_input)


async def confirm_phone_yes(_, __, manager: DialogManager):
    await manager.switch_to(DeliverySG.address_input)


async def confirm_phone_no(_, __, manager: DialogManager):
    await manager.switch_to(DeliverySG.phone_input)


async def confirm_address_yes(_, __, manager: DialogManager):
    await to_payment(_, __, manager)


async def confirm_address_no(_, __, manager: DialogManager):
    await manager.switch_to(DeliverySG.address_input)


async def delivery_getter(dialog_manager: DialogManager, **_kwargs):
    product_id = dialog_manager.start_data.get("product_id")
    product = next((p for p in PRODUCTS["bracelets"] if p["id"] == product_id), None)
    product_name = product["name"] if product is not None else "выбранный товар"
    return {
        "delivery_choice_text": DELIVERY_CHOICE_TEXT.format(product_name=product_name),
        "full_name": dialog_manager.dialog_data.get("full_name", ""),
        "phone": dialog_manager.dialog_data.get("phone", ""),
        "address": dialog_manager.dialog_data.get("address", ""),
        "delivery_method": dialog_manager.dialog_data.get("delivery_method", ""),
    }


delivery_dialog = Dialog(
    Window(
        Format("{delivery_choice_text}"),
        Button(Const("Почта"), id="delivery_post", on_click=set_post),
        Button(Const("Сдэк"), id="delivery_cdek", on_click=set_cdek),
        Button(Const("Назад"), id="back_product", on_click=back_to_product),
        state=DeliverySG.delivery,
        getter=delivery_getter,
    ),
    Window(
        Const("Введите Ф.И.О. Получателя:"),
        MessageInput(on_full_name_input),
        Button(Const("Назад"), id="back_delivery", on_click=back_delivery),
        state=DeliverySG.full_name_input,
    ),
    Window(
        Format("Вы Ввели Ф.И.О.: \"{full_name}\"\nВсе Верно?"),
        Button(Const("Подтвердить (Да)"), id="full_name_yes", on_click=confirm_full_name_yes),
        Button(Const("Нет, Изменить"), id="full_name_no", on_click=confirm_full_name_no),
        Button(Const("Назад"), id="back_delivery_2", on_click=back_delivery),
        state=DeliverySG.full_name_confirm,
        getter=delivery_getter,
    ),
    Window(
        Const("Введите Телефон (Допустимы Цифры И Символ +):"),
        MessageInput(on_phone_input),
        Button(Const("Назад"), id="back_full_name_confirm", on_click=to_full_name_confirm),
        state=DeliverySG.phone_input,
    ),
    Window(
        Format("Вы Ввели Телефон: \"{phone}\"\nВсе Верно?"),
        Button(Const("Подтвердить (Да)"), id="phone_yes", on_click=confirm_phone_yes),
        Button(Const("Нет, Изменить"), id="phone_no", on_click=confirm_phone_no),
        Button(Const("Назад"), id="back_phone_confirm", on_click=to_full_name_confirm),
        state=DeliverySG.phone_confirm,
        getter=delivery_getter,
    ),
    Window(
        Const("Введите Адрес (Индекс, Город, Улица, Дом, Квартира). Для Сдэк Можно Указать ПВЗ."),
        MessageInput(on_address_input),
        Button(Const("Назад"), id="back_phone", on_click=to_phone_confirm),
        state=DeliverySG.address_input,
    ),
    Window(
        Format("Способ Доставки: {delivery_method}\nВы Ввели Адрес: \"{address}\"\nВсе Верно?"),
        Button(Const("Подтвердить (Да)"), id="address_yes", on_click=confirm_address_yes),
        Button(Const("Нет, Изменить"), id="address_no", on_click=confirm_address_no),
        Button(Const("Назад"), id="back_address_confirm", on_click=to_phone_confirm),
        state=DeliverySG.address_confirm,
        getter=delivery_getter,
    ),
)
