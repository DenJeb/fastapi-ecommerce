# 09 — Saleor 官方资料调研笔记

> 调研基于 Saleor 官方仓库与官方文档公开内容。此文档是面向本学习项目的提炼，不是 Saleor 全量源码审计。正式开工前建议再选定一个稳定 release/tag，避免直接跟随可能变化的 main 分支。

## 1. Saleor 的定位

Saleor 是 API-first、headless commerce 平台，核心 API 使用 GraphQL。官方仓库介绍其覆盖产品目录、订单、客户、促销、支付、购物车/结算、多渠道、多仓库等能力。

对本项目的启示：
- 业务领域比单纯商品 CRUD 更广。
- API 设计与领域模型要分开思考；我们不必复刻 GraphQL。
- 多渠道、多币种、多仓库是高级复杂度，学习项目先收缩为单店铺单仓库。

## 2. 产品与变体

官方产品文档说明：
- 商品可有一个或多个 Product Variant。
- 价格与库存关联到 variant，而非只放在 product。
- SKU 用于唯一识别变体。
- 分类（Category）与集合（Collection）是不同概念：分类是层级结构，集合是灵活分组。

本项目采纳：
- `products` 与 `product_variants` 分表。
- SKU 唯一。
- 第一版每个商品一个分类；集合暂缓。
- 库存归属于 SKU/variant。

官方资料：[Product Overview](https://docs.saleor.io/developer/products/overview)

## 3. Checkout 与购物车

Saleor 官方 Checkout 文档有一个值得注意的设计：Saleor 没有独立的 Cart 模型；Checkout 对象同时承载购物车操作与结算信息，以便折扣、地址相关税费、配送估算等能力在同一对象中工作。Checkout 完成时可能处理支付、预留库存，并在满足条件后创建订单。

本项目不必照搬该模型。为了学习和理解边界，第一版使用 `carts` 与 `cart_items`，再由 checkout service 将购物车转换成订单。

需要理解的核心：
- 结算不只是“把购物车数据插入订单”。
- 结算需要重新校验价格、商品状态、库存、优惠和地址。
- 创建订单与库存预留必须有一致的事务策略。

官方资料：[Checkout Overview](https://docs.saleor.io/developer/checkout/overview)

## 4. 官方 API 领域划分

Saleor API Reference 按领域列出 Apps、Authentication、Channels、Checkout、Discounts、Orders、Payments、Products、Shipping、Users、Webhooks 等。

本学习项目优先映射：
- Authentication / Users -> auth、users
- Products -> catalog
- Checkout -> cart、checkout
- Orders -> orders
- Payments -> payments
- Discounts -> promotions

暂不实现 Channels、Shipping、Taxes、Apps、Webhooks 等高级领域。

官方资料：[API Reference](https://docs.saleor.io/api-reference)

## 5. 为什么不复刻 Saleor 的架构

Saleor 是成熟、复杂的 GraphQL commerce engine；本项目目标是训练 Python 后端工程基本功。直接完整重写会带来大量与当前学习目标无关的范围：
- GraphQL API 与复杂 schema
- 多渠道和多币种
- 多仓库与履约
- 支付编排与外部集成
- 复杂促销、税务、配送
- Apps 与 Webhooks 扩展机制

因此采用 FastAPI REST + MySQL + 模块化单体，保留有代表性的核心业务问题。

## 6. 官方参考链接

- Saleor Repository: https://github.com/saleor/saleor
- Saleor Documentation: https://docs.saleor.io/
- API Reference: https://docs.saleor.io/api-reference
- Product Overview: https://docs.saleor.io/developer/products/overview
- Checkout Overview: https://docs.saleor.io/developer/checkout/overview

## 7. 调研结论

本项目应从 Saleor 学习：
1. Product 与 Variant/SKU 的领域拆分。
2. 结算阶段统一校验商品、价格、优惠和库存。
3. 订单与支付是独立但协作的领域。
4. API-first 的模块边界与明确权限。
5. 高级能力应分阶段引入，不在第一版全部实现。

不应照搬：
- GraphQL API。
- Django 代码结构。
- Saleor 全量数据模型。
- 多渠道、多仓库、多币种和复杂企业级扩展。
