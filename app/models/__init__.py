"""
所有 ORM 模型统一入口
新增领域模型时在这里导入，Alembic autogenerate 和测试建表都依赖这个入口
"""
from app.models.migration_test import MigrationTest
from app.modules.auth.models import Role, User, user_roles
from app.modules.cart.models import Cart, CartItem
from app.modules.catalog.models import Category, Product, ProductVariant
from app.modules.inventory.models import Inventory, InventoryMovement, MovementType
from app.modules.orders.models import Order, OrderEvent, OrderItem, OrderStatus

__all__ = [
    "Cart",
    "CartItem",
    "Category",
    "Inventory",
    "InventoryMovement"
    "MigrationTest",
    "MovementType",
    "Order",
    "OrderEvent",
    "OrderItem",
    "OrderStatus",
    "Product",
    "ProductVariant",
    "Role",
    "User",
    "user_roles"
]