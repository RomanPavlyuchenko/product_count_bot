from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery

from tgbot.keyboards import kb_user
from tgbot.services import db_queries, service
from tgbot.services.texts import TEXTS


async def user_start(msg: Message, state: FSMContext):
    """Обработка команды старт"""
    await state.finish()
    user = await db_queries.get_user(msg.bot.get("db"), msg.from_user.id)
    if not user:
        await msg.answer(TEXTS["start"])
        await msg.answer("Оформить подписку", reply_markup=kb_user.subscribe())
        return
    await msg.answer("Выберите действие", reply_markup=kb_user.menu)


async def btn_subscribe(call: CallbackQuery):
    """Обработка команды на покупку подписки"""
    await call.answer()
    period = "день" if call.data == "day" else "месяц"
    await call.message.answer(f"Вы выбрали 1 {period} подписки")
    await call.message.answer(TEXTS["subscribe"], reply_markup=kb_user.paid())


async def paid(call: CallbackQuery, state: FSMContext):
    """Обработка команды 'Оплатил'. """
    await call.answer()
    await call.message.edit_reply_markup()
    await call.message.answer(TEXTS["paid"])


async def btn_add_product(call: CallbackQuery, state: FSMContext):
    """Обработка команды 'Добавить отслеживание'. """
    await call.answer()
    user = await db_queries.get_user(call.bot.get("db"), call.from_user.id)
    if not user:
        await call.message.answer(TEXTS["start"])
        return
    await call.message.edit_text("Жду артикул")
    await state.set_state("get_article")


async def get_article(msg: Message, state: FSMContext):
    """Ждет артикул товара, проверяет его количество на складе"""
    try:
        await state.update_data(article=int(msg.text))
    except ValueError:
        await msg.answer("Артикул должен быть числом")
        return
    amount = await service.get_stock_quantity(int(msg.text))
    if not amount:
        await msg.answer("Не удалось найти товар. Возможно вы ввели неправильный артикул")
        return
    await state.update_data(amount=amount)
    await msg.answer(f"Текущее количество товара - {amount}. Теперь введи минимальный остаток")
    await state.set_state("get_count")


async def get_count(msg: Message, state: FSMContext):
    """Ждет количество товара, которое нужно отслеживать и сохраняет отслеживание в БД"""
    try:
        count = int(msg.text)
    except ValueError:
        await msg.answer("Количество должно быть целым числом")
        return
    data = await state.get_data()
    await state.finish()
    await db_queries.add_new_tracking(
        session=msg.bot.get("db"),
        product_id=data["article"],
        count=count,
        user_id=msg.from_user.id
    )
    await msg.answer(f"Я сообщу когда этого товара останется всего {count} штук.", reply_markup=kb_user.menu)


async def send_my_tracking(msg: Message):
    """Реагирует на команду 'my_tracking'. Отправляет все отслеживания пользователя"""
    all_tracking = await db_queries.get_tracking_by_user_id(msg.bot.get("db"), msg.from_user.id)
    if not all_tracking:
        await msg.answer("У вас нет ни одного отслеживания")
        return
    text = "Ваши отслеживания:\n"
    for tracking in all_tracking:
        text += f"{tracking.product_id} - {tracking.count}\n"
    await msg.answer(text)


async def cmd_delete_tracking(msg: Message, state: FSMContext):
    await msg.answer("Введите артикул товара, который больше не нужно отслеживать")
    await state.set_state("get_scu_for_delete")


async def get_scu_for_delete(msg: Message, state: FSMContext):
    try:
        scu = int(msg.text)
    except TypeError:
        await msg.answer("Артикул должен быть числом")
        return
    await state.finish()
    result = await db_queries.delete_tracking(msg.bot.get("db"), scu, msg.from_user.id)
    if result:
        await msg.answer("Готово")
    else:
        await msg.answer("Такого отслеживания нет. Чтобы посмотреть свои отлеживания введите команду /my_tracking")


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    dp.register_callback_query_handler(btn_subscribe, lambda call: call.data == "day" or call.data == "month")
    dp.register_callback_query_handler(paid, lambda call: call.data == "paid")
    dp.register_callback_query_handler(btn_add_product, lambda call: call.data == "add")
    dp.register_message_handler(get_article, state="get_article")
    dp.register_message_handler(get_count, state="get_count")
    dp.register_message_handler(send_my_tracking, commands=["my_tracking"])
