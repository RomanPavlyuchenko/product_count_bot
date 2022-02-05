from datetime import date, timedelta

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, DBAPIError

from tgbot.models.tables import User, Tracking


async def add_new_tracking(session: AsyncSession, product_id: int, count: int, user_id: int):
    """Добавляет новое отслеживание"""
    await session.execute(sa.delete(Tracking).where(Tracking.user_id == user_id, Tracking.product_id == product_id))
    await session.commit()
    tracking = Tracking(user_id=user_id, product_id=product_id, count=count)
    session.add(tracking)
    try:
        await session.commit()
        return True
    except DBAPIError:
        await session.rollback()


async def add_user(session: AsyncSession, user_id: int, subscribe: int) -> bool:
    """
    Добавляет нового пользователя
    :param session:
    :param user_id:
    :param subscribe: Количество дней, на сколько активируется подписка у человека
    :return:
    """
    user = User(id=user_id, subscribe=date.today() + timedelta(days=subscribe))
    session.add(user)
    try:
        await session.commit()
        return True
    except (IntegrityError, DBAPIError):
        await session.rollback()
        return False


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """Возвращает объект пользователя если он есть в базе, иначе None"""
    user = await session.execute(sa.select(User).where(User.id == user_id))
    return user.scalar()


async def delete_user(session: AsyncSession, user_id: int) -> tuple | None:
    """Удаляет пользователя по его id"""
    result = await session.execute(sa.delete(User).where(User.id == user_id).returning("*"))
    await session.commit()
    return result.fitst()


async def delete_tracking(session: AsyncSession, product_id: int, user_id: int) -> tuple | None:
    """Удаляет отслеживание, которые выбрал пользователь"""
    result = await session.execute(
        sa.delete(Tracking).where(Tracking.product_id == product_id, Tracking.user_id == user_id).returning("*")
    )
    await session.commit()
    return result.fitst()


async def get_users(session: AsyncSession) -> list[User]:
    """Возвращает всех пользователей"""
    users = await session.execute(sa.select(User).order_by(User.id))
    return users.scalars().all()


async def remove_users_without_subscribe(session: AsyncSession):
    """Удаляет пользователей у которых срок подписки меньше сегодняшней даты"""
    await session.execute(sa.delete(User).where(User.subscribe < date.today()))
    await session.commit()


async def get_all_tracking(session: AsyncSession) -> list[Tracking]:
    """Возвращает все отслеживания в базе"""
    tracking = await session.execute(sa.select(Tracking).order_by(Tracking.user_id))
    return tracking.scalars().all()


async def get_tracking_by_user_id(session: AsyncSession, user_id: int) -> list[Tracking] | None:
    """Возвращает отслеживания пользователя"""
    tracking = await session.execute(sa.select(Tracking).where(Tracking.user_id == user_id))
    return tracking.scalars().all()


if __name__ == '__main__':
    import asyncio
    from tgbot.services.db_connection import get_session


    async def main():
        session = await get_session()
        requests = await delete_tracking(session, 123, 381428187)
        print(requests)
        await session.close()

    asyncio.run(main())

