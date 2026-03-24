---
name: perp-open-sop
description: 当用户询问“能不能开仓/可不可以开多或开空”时，使用标准化开仓检查流程，优先调用 perp_check_can_open。
---

# Goal
对“是否可以开仓”的问题，给出明确、可执行、低噪音的答案。

# Tools
- `perp_check_can_open`
- `perp_get_position`（仅在用户追问具体持仓细节时）
- `perp_get_open_orders`（仅在用户追问挂单细节时）

# SOP
1. 识别用户意图是否是“开仓可行性判断”。
2. 若缺少必要字段，先追问，不做额外查询。必要字段：
- `address`
- `coin`
- `side`（long/short）
- `size`
3. 必要字段齐全后，优先且只调用一次 `perp_check_can_open`。
4. 直接基于 `perp_check_can_open` 返回结果回答：
- `ok=true`：可以开仓，同时提示主要风险/注意事项。
- `ok=false`：逐条解释 `issues`，并把 `follow_up_question` 直接转成下一步提问。
5. 只有在用户明确要求明细时，才补充调用其他查询工具。

# Anti-Patterns
- 不要在调用 `perp_check_can_open` 之前，先并行调用 `perp_get_positions`、`perp_get_balance`、`perp_get_market_price`、`perp_get_coin_info`。
- 不要把“能不能开仓”问题拆成多工具手动拼接判断（避免重复和不一致）。

# Response Template
- 结论：可以 / 不可以
- 核心原因：最多 3 条（来自 `issues`）
- 下一步：给出 1 个最小行动（例如补充字段，或调整杠杆/数量）

