from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .service import get_stock_quantity_and_all_tracking, send_notification


scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def task_sending_notification(bot, session, **kwargs):
    """Задача по отправке уведомления, если товара на складе меньше, чем указал пользователь"""
    stock_quantity, all_tracking = await get_stock_quantity_and_all_tracking(session, **kwargs)
    await send_notification(bot, stock_quantity, all_tracking)


def add_jobs(bot, session):
    scheduler.add_job(task_sending_notification, "cron", hour=9, args=[bot, session])
    scheduler.add_job(task_sending_notification, "cron", hour=12, args=[bot, session], kwargs={'admins_only': True})
    scheduler.add_job(task_sending_notification, "cron", hour=20, args=[bot, session])
    # scheduler.add_job(task_sending_notification, "interval", minutes=2, args=[bot, session])
    return scheduler
