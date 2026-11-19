import datetime

import sqlalchemy
import sqlalchemy.orm

import app.db.session


def utc_now() -> datetime.datetime:
    """MySQL DATETIME 不保存时区，统一存 UTC 的 naive 时区"""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


user_roles = sqlalchemy.Table(
    "user_roles",
    app.db.session.Base.metadata,
    sqlalchemy.Column(
        "user_id",
        sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sqlalchemy.Column(
        "role_id",
        sqlalchemy.ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(app.db.session.Base):
    __tablename__ = "users"

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    email: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    username: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255),
        nullable=False,
    )
    is_active: sqlalchemy.orm.Mapped[bool] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Boolean,
        default=True,
        nullable=False,
    )
    created_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime,
        default=utc_now,
        nullable=False,
    )
    updated_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # selectin: 查询用户时一并加载角色
    roles: sqlalchemy.orm.Mapped[list["Role"]] = sqlalchemy.orm.relationship(
        secondary=user_roles,
        lazy="selectin",
    )


class Role(app.db.session.Base):
    __tablename__ = "roles"

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True,
    )
    name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32),
        unique=True,
        nullable=False,
    )
    description: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255),
        nullable=True,
    )