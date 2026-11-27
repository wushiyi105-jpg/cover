# 更新记录

## Unreleased

- 新增 `report`：年度保单体检 Markdown，含缺口、续费日历、理赔材料、条款红线
- 新增 `terms`：只返回能引用原文的免责条款，查不到明确拒答
- 8 类缺口公式、30 条免责条款、7 类理赔材料模板
- 模型条款解读改为结构化条目，原文对不上只丢那一条
- `0001_init` 改为显式 `op.create_table` / `op.create_index`，运行期走 `alembic upgrade`
- `app/` 只依赖 `ports`，新增内存假实现用例
- 开 ruff `E2`/`E3`；CI 增加 `docker build` 与 `/health` 探活

## 1.0.0

- 保额倍数与医疗定额
- 60 天宽限期与失效判定
- 理赔三件材料校验
- 同保单重复索赔检测
- 条款号与原文一致性守卫
