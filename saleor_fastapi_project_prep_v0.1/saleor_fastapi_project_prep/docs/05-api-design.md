# 05 — API 设计初稿

## 1. API 约定

- Base path：`/api/v1`
- 风格：REST；资源名使用复数名词。
- JSON 字段：`snake_case`。
- 认证：Bearer access token。
- 分页：`page`、`page_size`，默认 1 / 20，限制最大 100。
- 金额：以十进制字符串返回，避免客户端浮点精度误差。
- 错误响应统一结构：

```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Insufficient stock for one or more items",
    "details": {},
    "request_id": "..."
  }
}
```

## 2. 初步接口目录

### Auth / Users

| Method | Path | 权限 | 说明 |
|---|---|---|---|
| POST | /auth/register | Public | 注册 |
| POST | /auth/login | Public | 登录 |
| GET | /users/me | User | 当前用户 |
| PATCH | /users/me | User | 修改个人资料 |

### Catalog

| Method | Path | 权限 | 说明 |
|---|---|---|---|
| GET | /categories | Public | 分类列表 |
| GET | /products | Public | 商品列表/筛选 |
| GET | /products/{product_id} | Public | 商品详情 |
| POST | /admin/categories | Admin | 创建分类 |
| POST | /admin/products | Admin | 创建商品 |
| PATCH | /admin/products/{product_id} | Admin | 修改商品 |
| POST | /admin/products/{product_id}/variants | Admin | 创建 SKU |
| PATCH | /admin/variants/{variant_id} | Admin | 修改 SKU |

### Inventory

| Method | Path | 权限 | 说明 |
|---|---|---|---|
| GET | /admin/inventory | Admin | 库存查询 |
| POST | /admin/variants/{variant_id}/inventory-adjustments | Admin | 库存调整 |
| GET | /admin/inventory-movements | Admin | 库存流水 |

### Cart / Checkout

| Method | Path | 权限 | 说明 |
|---|---|---|---|
| GET | /cart | User | 获取购物车 |
| POST | /cart/items | User | 添加 SKU |
| PATCH | /cart/items/{item_id} | User | 修改数量 |
| DELETE | /cart/items/{item_id} | User | 删除购物车项 |
| POST | /checkout/preview | User | 结算预览 |
| POST | /checkout/orders | User | 创建订单 |

### Orders / Payments

| Method | Path | 权限 | 说明 |
|---|---|---|---|
| GET | /orders | User | 当前用户订单列表 |
| GET | /orders/{order_id} | Owner/Admin | 订单详情 |
| POST | /orders/{order_id}/cancel | Owner | 取消未支付订单 |
| POST | /orders/{order_id}/payments | Owner | 创建模拟支付 |
| POST | /payments/{payment_id}/simulate-result | Owner/Admin（开发环境限制） | 模拟支付结果 |
| POST | /admin/orders/{order_id}/fulfill | Admin | 标记完成 |
| POST | /admin/orders/{order_id}/refunds | Admin | 发起模拟退款 |

### Promotions（P1）

| Method | Path | 权限 | 说明 |
|---|---|---|---|
| GET | /coupons/available | User | 可用优惠券 |
| POST | /admin/coupons | Admin | 创建优惠券 |
| POST | /coupons/{coupon_id}/claim | User | 领取优惠券 |

## 3. 关键请求示例

### 添加购物车项

```json
{
  "variant_id": 101,
  "quantity": 2
}
```

### 创建订单

```json
{
  "shipping_address": {
    "recipient": "Example User",
    "phone": "13800000000",
    "province": "Example Province",
    "city": "Example City",
    "detail": "Example Road 1"
  },
  "coupon_code": null
}
```

请求头可包含 `Idempotency-Key`。服务端应基于用户和 key 防止重复创建订单。

### 订单响应（简化）

```json
{
  "id": 9001,
  "order_no": "ORD-EXAMPLE",
  "status": "PENDING_PAYMENT",
  "currency": "CNY",
  "subtotal": "199.00",
  "discount_total": "0.00",
  "total_amount": "199.00",
  "items": [
    {
      "product_name": "Example Product",
      "sku": "EXAMPLE-001",
      "unit_price": "99.50",
      "quantity": 2,
      "line_total": "199.00"
    }
  ]
}
```

## 4. API 安全约束

- 所有用户资源查询必须在服务端按当前用户过滤，不能仅依赖前端传入 user_id。
- 管理员接口统一依赖角色校验。
- 支付模拟结果接口只在本地开发配置启用，不能伪装成真实支付回调。
- 对订单创建、支付结果、取消订单等关键写接口设计幂等策略。
- 不在响应中暴露 password_hash、内部异常堆栈或敏感配置。
