import asyncio
import logging
from datetime import date, timedelta

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.utils.exceptions import ChatNotFound, BotBlocked

from tgbot.services.scheduler import task_sending_notification

from ..services import db_queries


async def begin_add_user(msg: Message, state: FSMContext):
    await msg.answer("Введи id пользователя")
    await state.set_state("get_id")


async def get_id_user(msg: Message, state: FSMContext):
    try:
        tg_id = int(msg.text)
    except ValueError:
        await msg.answer("Должны быть только цифры")
        return
    await state.update_data(telegram_id=tg_id)
    await msg.answer("Введи количество дней, на которое предоставлен доступ (Отправь только цифру. Если введешь 0, \
то пользователь будет добавлен на неограниченное количество дней)")
    await state.set_state("get_count_days")


async def get_count_days(msg: Message, state: FSMContext):
    try:
        days = int(msg.text)
    except ValueError:
        await msg.answer("Неверный формат")
        return
    data = await state.get_data()
    # subscribe = None if days == 0 else date.today() + timedelta(days=days)
    result = await db_queries.add_user(msg.bot.get("db"), data["telegram_id"], days)
    await state.finish()
    if not result:
        await msg.answer("Такой пользователь уже есть.")
        return
    await msg.answer("Готово")


async def begin_broadcaster(msg: Message, state: FSMContext):
    await msg.answer("Введи текст сообщения")
    await state.set_state("get_message")


async def sending_message(msg: Message, state: FSMContext):
    await state.finish()
    users = await db_queries.get_users(msg.bot.get("db"))
    for user in users:
        try:
            await msg.copy_to(user.id)
            await asyncio.sleep(1)
        except (ChatNotFound, BotBlocked) as er:
            logging.error(f"Не удалось отправить сообщение. Ошибка: {er}")
    await msg.answer("Готово")


async def get_count_users(msg: Message):
    users = await db_queries.get_users(msg.bot.get("db"))
    text = f"Количество пользователей: {len(users)}\n" + \
           "\n".join([f"{user.id} - {user.subscribe}" for user in users])
    await msg.answer(text)


async def delete_user(msg: Message, state: FSMContext):
    await msg.answer("Введи id пользователя")
    await state.set_state("get_id_for_delete")


async def get_id_for_delete(msg: Message, state: FSMContext):
    await state.finish()
    try:
        result = await db_queries.delete_user(msg.bot.get("db"), int(msg.text))
    except ValueError:
        await msg.answer("Введите только цифры")
        return
    if not result:
        await msg.answer("Такого пользователя нет")
    else:
        await msg.answer("Готово")

async def send_notification(msg: Message):
    await task_sending_notification(msg.bot, msg.bot['db'], admins_only=True)


def register_admin(dp: Dispatcher):
    dp.register_message_handler(begin_add_user, commands=["add_user"], state="*", is_admin=True)
    dp.register_message_handler(get_id_user, state="get_id")
    dp.register_message_handler(get_count_days, state="get_count_days")
    dp.register_message_handler(begin_broadcaster, commands=["sending"], is_admin=True)
    dp.register_message_handler(sending_message, state="get_message")
    dp.register_message_handler(get_count_users, commands=["count"], is_admin=True)
    dp.register_message_handler(delete_user, commands=["delete_user"], is_admin=True)
    dp.register_message_handler(get_id_for_delete, state="get_id_for_delete")
    dp.register_message_handler(send_notification, commands=["notification"], is_admin=True)
