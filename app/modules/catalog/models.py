import datetime
import decimal
import enum

import sqlalchemy
import sqlalchemy.orm

import app.core.time
import app.db.session


class ProductStatus(enum.StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Category(app.db.session.Base):
    __tablename__ = "categories"

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    parent_id: sqlalchemy.orm.Mapped[int | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(100),
        nullable=False,
    )
    slug: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    is_active: sqlalchemy.orm.Mapped[bool] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Boolean,
        default=True,
        nullable=False,
    )
    created_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime,
        default=app.core.time.utc_now,
        nullable=False,
    )
    updated_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime,
        default=app.core.time.utc_now,
        onupdate=app.core.time.utc_now,
        nullable=False,
    )


class Product(app.db.session.Base):
    __tablename__ = "products"

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    category_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(200),
        nullable=False,
    )
    slug: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(200),
        unique=True,
        index=True,
        nullable=False,
    )
    description: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Text,
        nullable=True,
    )
    status: sqlalchemy.orm.Mapped[ProductStatus] = sqlalchemy.orm.mapped_column(
        # native_enum=False: 用 varchar + check，修改枚举不用 alter enum
        sqlalchemy.Enum(
            ProductStatus,
            name="product_status",
            native_enum=False,
            length=20,
            create_constraint=True,
        ),
        default=ProductStatus.DRAFT,
        nullable=False,
        index=True,
    )
    created_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime,
        default=app.core.time.utc_now,
        nullable=False,
    )
    updated_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime,
        default=app.core.time.utc_now,
        onupdate=app.core.time.utc_now,
        nullable=False,
    )

    # selectin: 查商品时一并加载 SKU，避免 async 下的隐式懒加载
    variants: sqlalchemy.orm.Mapped[list["ProductVariant"]] = sqlalchemy.orm.relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ProductVariant(app.db.session.Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        sqlalchemy.CheckConstraint(
            "price >= 0",
            name="ck_product_variants_price_non_negative",
        ),
    )

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    product_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(100),
        nullable=False,
    )
    price: sqlalchemy.orm.Mapped[decimal.Decimal] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(12, 2),
        nullable=False,
    )
    is_active: sqlalchemy.orm.Mapped[bool] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Boolean,
        default=True,
        nullable=False,
    )
    created_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime,
        default=app.core.time.utc_now,
        nullable=False,
    )
    updated_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime,
        default=app.core.time.utc_now,
        onupdate=app.core.time.utc_now,
        nullable=False,
    )

    product: sqlalchemy.orm.Mapped["Product"] = sqlalchemy.orm.relationship(
        back_populates="variants",
    )