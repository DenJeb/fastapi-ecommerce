import datetime
import enum

import sqlalchemy
import sqlalchemy.orm

import app.core.time
import app.db.session


class MovementType(enum.StrEnum):
    ADJUST_IN = "ADJUST_IN"
    ADJUST_OUT = "ADJUST_OUT"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    SALE = "SALE"


class Inventory(app.db.session.Base):
    __tablename__ = "inventories"
    __table_args__ = (
        sqlalchemy.CheckConstraint(
            "on_hand >= 0",
            name="ck_inventories_on_hand_non_negative",
        ),
        sqlalchemy.CheckConstraint(
            "reserved >= 0",
            name="ck_inventories_reserved_non_negative",
        ),
        sqlalchemy.CheckConstraint(
            "reserved <= on_hand",
            name="ck_inventories_reserved_lte_on_hand",
        ),
    )

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    variant_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("product_variants.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    on_hand: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer,
        default=0,
        nullable=False,
    )
    reserved: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer,
        default=0,
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

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved


class InventoryMovement(app.db.session.Base):
    __tablename__ = "inventory_movements"

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    inventory_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("inventories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # orders 表尚未建立，先保留 order_id，后续迁移再补外键。
    order_id: sqlalchemy.orm.Mapped[int | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.BigInteger,
        nullable=True,
        index=True,
    )
    movement_type: sqlalchemy.orm.Mapped[MovementType] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Enum(
            MovementType,
            name="inventory_movement_type",
            native_enum=False,
            length=20,
            create_constraint=True,
        ),
        nullable=False,
        index=True,
    )
    quantity_delta: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer,
        nullable=False,
    )
    on_hand_after: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer,
        nullable=False,
    )
    reserved_after: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.Integer,
        nullable=False,
    )
    reason: sqlalchemy.orm.Mapped[str | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(255),
        nullable=True,
    )
    actor_user_id: sqlalchemy.orm.Mapped[int | None] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: sqlalchemy.orm.Mapped[datetime.datetime] = sqlalchemy.orm.mapped_column(
        sqlalchemy.DateTime,
        default=app.core.time.utc_now,
        nullable=False,
    )