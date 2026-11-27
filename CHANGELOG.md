# 更新记录

## Unreleased

- `0001_init` 改为显式 `op.create_table` / `op.create_index`，运行期走 `alembic upgrade`
- `app/` 只依赖 `ports`，新增内存假实现用例
- 开 ruff `E2`/`E3`；CI 增加 `docker build` 与 `/health` 探活

## 1.0.0

- 保额倍数与医疗定额
- 60 天宽限期与失效判定
- 理赔三件材料校验
- 同保单重复索赔检测
- 条款号与原文一致性守卫
