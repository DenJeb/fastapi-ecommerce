import datetime
import decimal
import enum

import sqlalchemy
import sqlalchemy.orm

import app.core.time
import app.db.session


class OrderStatus(enum.StrEnum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    REFUND_PENDING = "REFUND_PENDING"
    REFUNDED = "REFUNDED"
    FULFILLED = "FULFILLED"


class Order(app.db.session.Base):
    __tablename__ = "orders"
    __table_args__ = (
        sqlalchemy.UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_orders_user_idempotency_key",
        ),
        sqlalchemy.Index(
            "ix_orders_user_created",
            "user_id",
            "created_at",
        ),
        sqlalchemy.CheckConstraint(
            "subtotal >= 0",
            name="ck_orders_subtotal_non_negative",
        ),
        sqlalchemy.CheckConstraint(
            "discount_total >= 0",
            name="ck_orders_discount_total_non_negative",
        ),
        sqlalchemy.CheckConstraint(
            "total_amount >= 0",
            name="ck_orders_total_amount_non_negative",
        ),
    )

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    order_no: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(32),
        unique=True,
        index=True,
        nullable=False,
    )
    user_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: sqlalchemy.orm.Mapped[OrderStatus] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Enum(
            OrderStatus,
            name="order_status",
            native_enum=False,
            length=20,
            create_constraint=True,
        ),
        default=OrderStatus.PENDING_PAYMENT,
        nullable=False,
        index=True,
    )
    currency: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(3),
        default="CNY",
        nullable=False,
    )
    subtotal: sqlalchemy.orm.Mapped[decimal.Decimal] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(12, 2),
        nullable=False,
    )
    discount_total: sqlalchemy.orm.Mapped[decimal.Decimal] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(12, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    total_amount: sqlalchemy.orm.Mapped[decimal.Decimal] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(12, 2),
        nullable=False,
    )
    idempotency_key: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(64),
        nullable=True,
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
    cancelled_at: sqlalchemy.orm.Mapped[datetime.datetime | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime,
        nullable=True,
    )

    items: sqlalchemy.orm.Mapped[list["OrderItem"]] = sqlalchemy.orm.relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    events: sqlalchemy.orm.Mapped[list["OrderEvent"]] = sqlalchemy.orm.relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class OrderItem(app.db.session.Base):
    __tablename__ = "order_items"
    __table_args__ = (
        sqlalchemy.CheckConstraint(
            "quantity > 0",
            name="ck_order_items_quantity_positive",
        ),
        sqlalchemy.CheckConstraint(
            "unit_price >= 0",
            name="ck_order_items_unit_price_non_negative",
        ),
        sqlalchemy.CheckConstraint(
            "line_total >= 0",
            name="ck_order_items_line_total_non_negative",
        ),
    )

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    order_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 允许商品/SKU 删除后保留历史订单。
    variant_id: sqlalchemy.orm.Mapped[int | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey(
            "product_variants.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )
    product_name_snapshot: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(200),
        nullable=False,
    )
    sku_snapshot: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(64),
        nullable=False,
    )
    variant_name_snapshot: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(100),
        nullable=False,
    )
    unit_price: sqlalchemy.orm.Mapped[decimal.Decimal] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(12, 2),
        nullable=False,
    )
    quantity: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer,
        nullable=False,
    )
    line_total: sqlalchemy.orm.Mapped[decimal.Decimal] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Numeric(12, 2),
        nullable=False,
    )
    created_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime,
        default=app.core.time.utc_now,
        nullable=False,
    )

    order: sqlalchemy.orm.Mapped["Order"] = sqlalchemy.orm.relationship(
        back_populates="items",
    )

    @property
    def product_name(self) -> str:
        return self.product_name_snapshot

    @property
    def sku(self) -> str:
        return self.sku_snapshot

    @property
    def variant_name(self) -> str:
        return self.variant_name_snapshot


class OrderEvent(app.db.session.Base):
    __tablename__ = "order_events"

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    order_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: sqlalchemy.orm.Mapped[OrderStatus | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Enum(
            OrderStatus,
            name="order_event_from_status",
            native_enum=False,
            length=20,
            create_constraint=True,
        ),
        nullable=True,
    )
    to_status: sqlalchemy.orm.Mapped[OrderStatus] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Enum(
            OrderStatus,
            name="order_event_to_status",
            native_enum=False,
            length=20,
            create_constraint=True,
        ),
        nullable=False,
    )
    actor_user_id: sqlalchemy.orm.Mapped[int | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reason: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255),
        nullable=True,
    )
    created_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime,
        default=app.core.time.utc_now,
        nullable=False,
    )

    order: sqlalchemy.orm.Mapped["Order"] = sqlalchemy.orm.relationship(
        back_populates="events",
    )