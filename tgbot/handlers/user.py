import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery

from tgbot.keyboards import kb_user
from tgbot.services import db_queries, service
from tgbot.services.texts import TEXTS
from tgbot.config import config



async def check_subscribe(message: Message):
    if await message.bot.get_chat_member(
            chat_id=config.tg.chat_id,
            user_id=message.from_user.id
    ):
        return True
    else:
        await message.answer(TEXTS['not_subscribed'], parse_mode='MarkdownV2')
        return False

async def user_start(msg: Message, state: FSMContext):
    """Обработка команды старт"""
    await state.finish()
    if not await check_subscribe(msg):
        return
    user = await db_queries.get_user(msg.bot.get("db"), msg.from_user.id)
    if not user:
        await msg.answer(TEXTS["start"])
        await msg.answer("Оформить подписку", reply_markup=kb_user.subscribe())
        return
    await msg.answer("Выберите действие", reply_markup=kb_user.menu)


# async def btn_subscribe(call: CallbackQuery):
#     """Обработка команды на покупку подписки"""
#     await call.answer()
#     period = "день" if call.data == "day" else "месяц"
#     await call.message.answer(f"Вы выбрали 1 {period} подписки")
#     await call.message.answer(TEXTS["subscribe"], reply_markup=kb_user.paid())


# async def paid(call: CallbackQuery, state: FSMContext):
#     """Обработка команды 'Оплатил'. """
#     await call.answer()
#     await call.message.edit_reply_markup()
#     await call.message.answer(TEXTS["paid"])


async def btn_add_product(call: CallbackQuery, state: FSMContext):
    """Обработка команды 'Добавить отслеживание'. """
    if not await check_subscribe(call):
        return
    await call.answer()
    user = await db_queries.get_user(call.bot.get("db"), call.from_user.id)
    if not user:
        await call.message.answer(TEXTS["start"])
        return
    await call.message.edit_text("Жду артикул")
    await state.set_state("get_article")


async def get_article(msg: Message, state: FSMContext):
    """Ждет артикул товара, проверяет его количество на складе"""
    if not await check_subscribe(msg):
        return
    try:
        await state.update_data(article=int(msg.text))
    except ValueError:
        await msg.answer("Артикул должен быть числом")
        return
    logging.info(int(msg.text))
    amount, size_d = await service.get_stock_quantity(int(msg.text))
    if not amount:
        await msg.answer("Не удалось найти товар. Возможно вы ввели неправильный артикул")
        return

    await state.update_data(amount=amount)
    await state.update_data(size=size_d)

    if len(size_d) < 2:
        await msg.answer(f"Текущее количество товара - {amount}\nВведите минимальный остаток")
        await state.set_state("get_count")

    else:
        size_txt = await service.dict_convert_text(size_d)
        await msg.answer(f"Текущее количество товара - {amount}\nРазмеры:\n{size_txt}\nВведите минимальный остаток")
        await state.set_state("get_size")


async def get_count(msg: Message, state: FSMContext):
    if not await check_subscribe(msg):
        return
    count_size = -1
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
        count_size=count_size,
        user_id=msg.from_user.id
    )
    await msg.answer(f"Я сообщу когда этого товара останется всего {count} штук.", reply_markup=kb_user.menu)

async def send_my_tracking(msg: Message):
    if not await check_subscribe(msg):
        return
    """Реагирует на команду 'my_tracking'. Отправляет все отслеживания пользователя"""
    all_tracking = await db_queries.get_tracking_by_user_id(msg.bot.get("db"), msg.from_user.id)
    if not all_tracking:
        await msg.answer("У вас нет ни одного отслеживания")
        return
    text = "Ваши отслеживания:\n"

    for tracking in all_tracking:
        if tracking.count_size == -1:
            text += f"{tracking.product_id} - {tracking.count}\n"
        else:
            text += f"{tracking.product_id} - {tracking.count} - {tracking.count_size}\n"
    await msg.answer(text)


async def cmd_delete_tracking(msg: Message, state: FSMContext):
    await msg.answer("Введите артикул товара, который больше не нужно отслеживать")
    await state.set_state("get_scu_for_delete")


async def get_scu_for_delete(msg: Message, state: FSMContext):
    if not await check_subscribe(msg):
        return
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

async def btn_get_remains(call: CallbackQuery, state: FSMContext):
    """Обработка команды 'Узнать остаток'. """
    if not await check_subscribe(call):
        return
    await call.answer()
    user = await db_queries.get_user(call.bot.get("db"), call.from_user.id)
    if not user:
        await call.message.answer(TEXTS["start"])
        return
    await call.message.edit_text("Жду артикул")
    await state.set_state("get_article_remains")


async def get_article_remains(msg: Message, state: FSMContext):
    """Ждет артикул товара, проверяет его количество на складе"""
    try:
        article = int(msg.text)
    except ValueError:
        await msg.answer("Артикул должен быть числом")
        return
    amount, size_d = await service.get_stock_quantity(int(msg.text))
    size_txt = await service.dict_convert_text(size_d)
    if not amount:
        await msg.answer("Не удалось найти товар. Возможно вы ввели неправильный артикул")
        return

    if len(size_d) < 2:
        await msg.answer(f"Текущее количество товара - {amount}", reply_markup=kb_user.menu)
    else:
        await msg.answer(f"Текущее количество товара - {amount}.Размеры\n{size_txt}", reply_markup=kb_user.menu)

    await state.finish()


async def get_size(msg: Message, state: FSMContext):
    try:
        count = int(msg.text)
    except ValueError:
        await msg.answer("Количество должно быть целым числом")
        return
    await msg.answer("Укажите остаток на один размер, либо пропустите этот шаг", reply_markup=kb_user.skip)
    await state.update_data(count=count)
    await state.set_state('save_db')

async def skip(call: CallbackQuery, state: FSMContext):
    """Ждет количество товара, которое нужно отслеживать и сохраняет отслеживание в БД"""
    data = await state.get_data()
    count_size = -1
    await call.message.answer(
        f"Я сообщу когда этого товара останется всего {data['count']} штук",
        reply_markup=kb_user.menu)

    await state.finish()
    await db_queries.add_new_tracking(
        session=call.bot.get("db"),
        product_id=data["article"],
        count=data['count'],
        count_size=count_size,
        user_id=call.from_user.id
    )

async def save_db(msg: Message, state: FSMContext):
    """Ждет количество товара, которое нужно отслеживать и сохраняет отслеживание в БД"""
    data = await state.get_data()
    try:
        count_size = int(msg.text)
    except ValueError:
        await msg.answer("Количество должно быть целым числом")
        return

    await msg.answer(
        f"Я сообщу когда этого товара останется всего {data['count']} штук. Либо остаток по размеру составит {count_size} штук",
        reply_markup=kb_user.menu)

    await state.finish()
    await db_queries.add_new_tracking(
        session=msg.bot.get("db"),
        product_id=data["article"],
        count=data['count'],
        count_size = count_size,
        user_id=msg.from_user.id
    )

def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")
    # dp.register_callback_query_handler(btn_subscribe, lambda call: call.data == "day" or call.data == "month")
    # dp.register_callback_query_handler(paid, lambda call: call.data == "paid")
    dp.register_callback_query_handler(btn_add_product, lambda call: call.data == "add")
    dp.register_callback_query_handler(btn_get_remains, lambda call: call.data == "remains")
    dp.register_callback_query_handler(skip, lambda call: call.data == "skip", state="save_db")
    dp.register_message_handler(get_article_remains, state="get_article_remains")
    dp.register_message_handler(get_article, state="get_article")
    dp.register_message_handler(get_count, state="get_count")
    dp.register_message_handler(send_my_tracking, commands=["my_tracking"])
    dp.register_message_handler(cmd_delete_tracking, commands=["delete_tracking"])
    dp.register_message_handler(get_scu_for_delete, state="get_scu_for_delete")
    dp.register_message_handler(get_size, state="get_size")
    dp.register_message_handler(save_db, state="save_db")

