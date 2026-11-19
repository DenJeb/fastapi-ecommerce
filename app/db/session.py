import sqlalchemy
import sqlalchemy.ext.asyncio

from app.core.config import settings


# 使用 url.create 构建链接地址，自动处理密码中的特殊字符
database_url = sqlalchemy.URL.create(
    drivername="mysql+asyncmy",
    username=settings.db_user,
    password=settings.db_password.get_secret_value(),
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)

# 创建异步引擎
engine = sqlalchemy.ext.asyncio.create_async_engine(
    database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

# 创建异步 session 
async_session_factory = sqlalchemy.ext.asyncio.async_sessionmaker(
    bind=engine,
    class_=sqlalchemy.ext.asyncio.AsyncSession,
    expire_on_commit=False,
)

# 所有 ORM 模型统一继承该基类
class Base(sqlalchemy.orm.DeclarativeBase):
    pass