# Cover · 家庭保单

[![test](https://github.com/wushiyi105-jpg/cover/workflows/test/badge.svg)](https://github.com/wushiyi105-jpg/cover/actions)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

![示例](assets/demo.gif)

一家人的保单摊开：谁缺多少保额、哪张进了宽限期、理赔材料缺哪张。

## 为什么不用一张 Excel

保单的麻烦不在保费，在「够不够」和「有没有断」。寿险按年收入 10 倍、重疾 3 倍、意外 5 倍、医疗按 30 万定额，
和已买的保额一比，缺口就是数字；到期后 60 天宽限期，过了就失效；理赔三件材料缺一件就打回。
模型可以写解读，但引条款必须把条款号和原文一起带上，对不上就删。

## 它做什么

1. **保额缺口**：按倍数与定额算建议，逐人逐险种比差额。
2. **宽限期**：到期前 15 天提示，逾期 60 天内算宽限，超过判失效。
3. **理赔材料**：诊断证明、发票、费用清单三件套缺项列出。
4. **重复索赔**：同一张保单两条索赔直接报。
5. **条款守卫**：引条款不给号、或号对不上原文，整句丢弃。

## 怎么用

```bash
pip install -e ".[dev]"
python -m cover seed
python -m cover audit --day 2026-11-27
python -m cover renew --day 2026-11-27
python -m cover serve        # http://127.0.0.1:8004
```

真实种子：3 人（本人年收入 18 万、配偶 15 万、女儿 0）、5 张保单、3 条理赔。
以 2026-11-27 跑 `audit`：8 项缺口合计 4,440,000 元，最大一档是配偶寿险差 150 万；
重疾那张宽限第 38 天、医疗那张宽限第 12 天；两条理赔各缺材料，且 #2 与 #1 撞同一张保单。
扣分 62（8×5 缺口 + 2×4 宽限 + 2×4 材料 + 6 重复索赔）。

## 规则与扣分

| rule_id | 含义 | 扣分 |
| --- | --- | --- |
| `cover.gap` | 某险种保额低于建议 | 5 |
| `policy.grace` | 进入 60 天宽限期 | 4 |
| `policy.lapsed` | 超过宽限期已失效 | 12 |
| `claim.docs` | 理赔材料缺项 | 4 |
| `claim.dup` | 同保单重复索赔 | 6 |
| `guard.terms` | 条款号与原文对不上 | 8 |

## 边界

- 保额倍数只是通用口径，不替代核保结论；
- 不计算免赔额与赔付比例；
- 不做产品推荐。

## 作者

shiyi · GitHub [@wushiyi105-jpg](https://github.com/wushiyi105-jpg) · wushiyi105@gmail.com
