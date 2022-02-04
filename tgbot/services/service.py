import asyncio
import logging
import random

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from .db_queries import get_all_tracking, add_new_tracking
from .wb import get_product_info
from ..models.models import Product
from ..models.tables import Tracking


def get_unique_product_ids(all_tracking: list[Tracking]) -> set[int]:
    """Возвращает из списка отслеживания только уникальные товары"""
    unique_product = set(tracking.product_id for tracking in all_tracking)
    return unique_product


def calculate_stock_quantity(product: Product) -> int:
    """Считает количество оставшегося товара из данных полученных от WB"""
    amount = 0
    for size in product.sizes:
        for stock in size.stocks:
            amount += stock.qty
    return amount


async def get_stock_quantity_for_products(unique_product_ids: set[int]) -> dict:
    """Возвращает словарь с артикулом товара и его количеством на складе"""
    result = {}
    for product_id in unique_product_ids:
        product = await get_product_info(product_id)
        if not product:
            continue
        amount = calculate_stock_quantity(product)
        if amount:
            result[product_id] = amount
        await asyncio.sleep(random.randint(2, 4))
    return result


async def get_stock_quantity_and_all_tracking(session: AsyncSession) -> tuple[dict, list[Tracking]]:
    """Возвращает словарь с товарами и их количество на складе и список всех отслеживаний"""
    all_tracking = await get_all_tracking(session)
    unique_products = get_unique_product_ids(all_tracking)
    stock_quantity_products = await get_stock_quantity_for_products(unique_products)
    return stock_quantity_products, all_tracking


async def send_notification(bot: Bot, stock_quantity: dict, all_tracking: list[Tracking]):
    """Отправляет уведомление о том, сколько товара на складе, если его меньше, чем указал пользователь"""
    for tracking in all_tracking:
        logging.info(f"SCU - {tracking.product_id}. Count - {tracking.count}. "
                     f"Stock - {stock_quantity.get(tracking.product_id, float('inf'))}")
        if tracking.count >= stock_quantity.get(tracking.product_id, float("inf")):
            text = f"Товара с артикулом {tracking.product_id} осталось - {stock_quantity[tracking.product_id]}"
            await bot.send_message(tracking.user_id, text)


async def get_stock_quantity(product_id) -> int | None:
    """Функция возвращает количество товара на складе или None, если не удалось найти товар"""
    product_info = await get_product_info(product_id)
    if not product_info:
        return
    amount = calculate_stock_quantity(product_info)
    return amount


async def save_new_tracking(session, product_id, count, user_id) -> int | None:
    """Сохранение нового отслеживания"""
    product_info = await get_product_info(product_id)
    if not product_info:
        return
    amount = calculate_stock_quantity(product_info)
    await add_new_tracking(session, product_id, count, user_id)
    return amount



