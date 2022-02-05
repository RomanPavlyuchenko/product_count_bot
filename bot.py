import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat
from aiogram.utils.exceptions import ChatNotFound

from tgbot.config import Settings
from tgbot.filters.admin import AdminFilter
from tgbot.handlers.admin import register_admin
from tgbot.handlers.user import register_user
from tgbot.services.db_connection import get_session
from tgbot.services.logger import setup_logger
from tgbot.services.scheduler import add_jobs


def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)


def register_all_handlers(dp):
    register_admin(dp)
    register_user(dp)


async def set_commands(dp: Dispatcher):
    config = dp.bot.get('config')
    admin_ids = config.tg.admins
    await dp.bot.set_my_commands(
        commands=[BotCommand('start', 'Старт'), BotCommand("my_tracking", "Мои отслеживания"),
                  BotCommand("delete_tracking", "Удалить отслеживание")]
    )
    commands_for_admin = [
        BotCommand('start', 'Старт'),
        # BotCommand("help", "Руководство пользователя"),
        BotCommand("add_user", "Добавить пользователя бота"),
        BotCommand("sending", "Рассылка сообщения пользователям"),
        BotCommand("count", "Количество пользователей"),
        BotCommand("delete_user", "Удалить пользователя"),
        BotCommand("my_tracking", "Мои отслеживания"),
        BotCommand("delete_tracking", "Удалить отслеживание"),
    ]
    for admin_id in admin_ids:
        try:
            await dp.bot.set_my_commands(
                commands=commands_for_admin,
                scope=BotCommandScopeChat(admin_id)
            )
        except ChatNotFound as er:
            logging.error(f'Установка команд для администратора {admin_id}: {er}')


async def main():
    setup_logger("INFO")
    config = Settings()
    logging.info("Starting Bot")

    # if config.tg.use_redis:
    #     storage = RedisStorage()
    # else:
    storage = MemoryStorage()

    bot = Bot(token=config.tg.token, parse_mode='HTML')
    dp = Dispatcher(bot, storage=storage)

    bot['config'] = config
    bot['db'] = db_session = await get_session()
    bot.set_current(bot)
    bot_info = await bot.get_me()
    logging.info(f'<yellow>Name: <b>{bot_info["first_name"]}</b>, username: {bot_info["username"]}</yellow>')

    # register_all_middlewares(dp)
    register_all_filters(dp)
    register_all_handlers(dp)
    await set_commands(dp)
    scheduler = add_jobs(bot, db_session)

    # start
    try:
        scheduler.start()
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        session = await bot.get_session()
        await session.close()
        # await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
