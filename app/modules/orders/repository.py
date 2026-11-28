import sqlalchemy
import sqlalchemy.ext.asyncio

import app.modules.orders.models as order_models


class OrderRepository:
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession):
        self.session = session

    async def get_by_idempotency_key(self, user_id: int, key: str) -> order_models.Order | None:
        result = await self.session.execute(
            sqlalchemy.select(order_models.Order).where(
                order_models.Order.user_id == user_id,
                order_models.Order.idempotency_key == key,
            )
        )
        return result.scalar_one_or_none()

    def add(self, order: order_models.Order) -> None:
        self.session.add(order)