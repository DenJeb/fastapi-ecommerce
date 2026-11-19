import logging

import fastapi
import sqlalchemy
import sqlalchemy.exc
import sqlalchemy.ext.asyncio

import app.db.dependencies

logger = logging.getLogger(__name__)

router = fastapi.APIRouter()


@router.get("/health", tags=["Health"])
async def health_check(
    db_session: sqlalchemy.ext.asyncio.AsyncSession = fastapi.Depends(
        app.db.dependencies.get_db_session
    ),
):
    """验证 API 与数据库连接是否可用"""
    try:
        await db_session.execute(sqlalchemy.text("SELECT 1"))
    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception("Health check database probe failed")
        raise fastapi.HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        )

    return {
        "status": "OK",
        "database": "OK",
    }