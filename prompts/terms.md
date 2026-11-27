基于给出的成员、保单、缺口写一段条款体检解读，只输出 JSON：
{"summary": "三句以内总体判断",
 "items": [{"policy_id": 1, "clause_no": "3.2", "clause_text": "保单原文，一字不改", "meaning": "这句话对理赔意味着什么，20 字内"}]}

- clause_no 与 clause_text 必须来自 facts 里的 policies，且原文不得改写；
- 引不到原文就不要写这条 item；
- 只引用 facts 里的数字，不推测能否理赔；
- 不评价保险公司，不给投保推荐。
