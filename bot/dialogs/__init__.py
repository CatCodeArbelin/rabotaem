"""Публичные экспорты диалогов бота."""

from .catalog import catalog_dialog
from .delivery import delivery_dialog
from .main_menu import main_menu_dialog
from .payment import payment_dialog
from .product import product_dialog

__all__ = [
    "main_menu_dialog",
    "catalog_dialog",
    "product_dialog",
    "delivery_dialog",
    "payment_dialog",
]
