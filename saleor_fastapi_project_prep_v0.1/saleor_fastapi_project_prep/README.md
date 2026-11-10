# Saleor-inspired Commerce Backend (FastAPI) — 项目前期设计包

> 版本：v0.1（开工前基线）  
> 项目性质：个人学习 / 作品集项目；不面向真实商业运营，不以公网部署为目标。  
> 实现约束：最终由 Python + FastAPI 独立实现；Saleor 仅作为业务与架构研究对象，不复制其 Django/GraphQL 实现。

## 文档导航

1. [项目说明书](docs/01-project-brief.md)
2. [需求规格说明书](docs/02-requirements.md)
3. [业务流程与领域模型](docs/03-business-design.md)
4. [数据库设计](docs/04-database-design.md)
5. [API 设计初稿](docs/05-api-design.md)
6. [技术架构与决策](docs/06-architecture.md)
7. [测试计划与验收标准](docs/07-testing.md)
8. [开发路线与任务清单](docs/08-roadmap.md)
9. [Saleor 调研笔记](docs/09-saleor-research.md)

## 当前设计边界

- 第一阶段只做后端，不开发完整前端。
- MySQL 是主数据库；Redis 在核心业务跑通后引入。
- 支付仅做模拟支付，不接真实支付网关。
- 不实现多渠道、多币种、多仓库、复杂税务、真实物流、Marketplace、多租户。
- 先实现单店铺、单币种、单仓库的可解释业务闭环。
- 所有库存数量、订单金额、状态变化必须有明确业务规则和测试。

## 如何使用

- 先阅读 01–03，确认业务边界。
- 再校正 04–06，形成数据库与 API 设计。
- 开发时以 08 的里程碑推进，每个模块完成 07 中对应测试。
- 设计与实现不一致时，更新文档并记录 ADR，不要让文档长期失真。

## 重要说明

这是可执行的初始设计基线，不是对 Saleor 的完整规格复刻。部分业务规则（例如库存预留超时、取消订单窗口）属于本学习项目的明确设计选择，需要在实现前确认并通过测试固定下来。
