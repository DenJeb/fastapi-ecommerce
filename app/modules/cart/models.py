import datetime
import decimal

import sqlalchemy
import sqlalchemy.orm

import app.core.time
import app.db.session
import app.modules.catalog.models as catalog_models


class Cart(app.db.session.Base):
    __tablename__ = "carts"

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    user_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
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

    items: sqlalchemy.orm.Mapped[list["CartItem"]] = sqlalchemy.orm.relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def subtotal(self) -> decimal.Decimal:
        return sum(
            (item.line_total for item in self.items),
            decimal.Decimal("0.00"),
        )

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.items)


class CartItem(app.db.session.Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        sqlalchemy.UniqueConstraint(
            "cart_id",
            "variant_id",
            name="uq_cart_items_cart_variant",
        ),
        sqlalchemy.CheckConstraint(
            "quantity > 0",
            name="ck_cart_items_quantity_positive",
        )
    )

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    cart_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer,
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

    cart: sqlalchemy.orm.Mapped["Cart"] = sqlalchemy.orm.relationship(
        back_populates="items",
    )
    variant: sqlalchemy.orm.Mapped[catalog_models.ProductVariant] = (
        sqlalchemy.orm.relationship(lazy="selectin")
    )

    @property
    def sku(self) -> str:
        return self.variant.sku

    @property
    def name(self) -> str:
        return self.variant.name

    @property
    def unit_price(self) -> decimal.Decimal:
        return self.variant.price

    @property
    def line_total(self) -> decimal.Decimal:
        return self.variant.price * self.quantity