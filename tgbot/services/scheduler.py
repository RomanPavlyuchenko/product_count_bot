from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .service import get_stock_quantity_and_all_tracking, send_notification


scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def task_sending_notification(bot, session):
    stock_quantity, all_tracking = await get_stock_quantity_and_all_tracking(session)
    await send_notification(bot, stock_quantity, all_tracking)


def add_jobs(bot, session):
    scheduler.add_job(task_sending_notification, "cron", hour=9, args=[bot, session])
    scheduler.add_job(task_sending_notification, "cron", hour=12, args=[bot, session])
    scheduler.add_job(task_sending_notification, "cron", hour=20, args=[bot, session])
    scheduler.add_job(task_sending_notification, "cron", hour=20, minute=30, args=[bot, session])
    # scheduler.add_job(task_sending_notification, "interval", hours=2, args=[bot, session])
    return scheduler
