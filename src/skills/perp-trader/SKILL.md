---
name: perp-trader
description: 当 interact_mode=frontend 时，使用 action tools 生成 confirm card。
---

# Goal

在 `interact_mode=frontend` 模式下，完成 Perp 交易的意图识别、参数收集、confirm card 生成。

# Intent Routing Table

| 意图关键词 | Tool | 说明 |
|-----------|------|------|
| 做多，做空，开仓，做多 BTC | confirm_perp_open_order | 开仓 |
| 平仓，平多头，平空头 | confirm_perp_close_position | 平仓 |
| 转入，转出，存款，提款，往合约 | confirm_perp_transfer | 资金划转 |
| 止盈，止损，设置 tpsl | confirm_set_tpsl | 止盈止损 |
| 仓位，持仓，当前 | view_position | 查看仓位 |

# WORKFLOW

## Step 1: Recognize Intent

根据用户输入，匹配上方 Intent Routing Table，选定对应 Tool。

## Step 2: Feasibility Check & Parameter Collection

### 开仓 (confirm_perp_open_order)

- **约束**：每轮对话只能开一个 coin，多个意图时按 coin 名升序选第一个
- **参数来源**：参考 [confirm_perp_open_order 参数详解](resources/confirm_perp_open_order.md)
- **必填参数**：coin、leverage、usdc_size、side
- **可选参数**：tp/sl（价格）、tp_ratio/sl_ratio（比例）、order_type、entry_price、margin_mode
- **参数不全时**：主动追问用户，不自行查询

### 平仓 (confirm_perp_close_position)

- **前置检查**：
  - 用户提及了具体 coin → 调用 `perp_get_positions(address, coin=xxx)` 获取该 coin 的仓位
  - 用户没有提及 coin → 调用 `perp_get_positions(address)` 获取所有仓位，遍历处理
- **约束**：无，每轮可批量平多个 coin
- **参数来源**：参考 [confirm_perp_close_position 参数详解](resources/confirm_perp_close_position.md)
- **必填参数**：closes（list，含 coin、position_side、position_size）
- **参数不全时**：主动追问用户，不自行查询

### 资金划转 (confirm_perp_transfer)

- **参数来源**：参考 [confirm_perp_transfer 参数详解](resources/confirm_perp_transfer.md)
- **必填参数**：action_type（PERPS_DEPOSIT / PERPS_WITHDRAW）、amount
- **参数不全时**：主动追问用户，不自行查询

### 止盈止损 (confirm_set_tpsl)

- **前置检查**：
  - 用户提及了具体 coin → 调用 `perp_get_positions(address, coin=xxx)` 获取该 coin 的仓位
  - 用户没有提及 coin → 先追问用户要设置哪个 coin（TPSL 不支持批量）
- **查询已有订单**：调用 `perp_get_open_orders(address, coin=xxx)` 查该 coin 是否有现有 TPSL 订单
  - 若有，在参数中填入 `existing_tp_oid` / `existing_sl_oid`
  - 若无，`existing_tp_oid` / `existing_sl_oid` 均填 `0`
- **只设止盈**：tp_price 或 tp_ratio 二选一，止损相关参数全部填 None
- **只设止损**：sl_price 或 sl_ratio 二选一，止盈相关参数全部填 None
- **参数不全时**：主动追问用户，不自行查询

## Step 3: Validate Parameters

调用 tool 前，验证关键约束：

- tp 和 tp_ratio 互斥（二选一）
- sl 和 sl_ratio 互斥（二选一）
- leverage 必须 > 0
- usdc_size 必须 > 0
- coin 必须是有效币种

**验证失败**：直接告知用户问题所在，不调用 tool。

## Step 4: Generate Confirm Card

验证通过后，调用对应 action tool，返回 confirm card 等待用户确认。

# Tools

| Tool | 用途 |
|------|------|
| confirm_perp_open_order | 开仓（做多/做空） |
| confirm_perp_close_position | 平仓（支持批量平多个 coin） |
| confirm_perp_transfer | 资金划转（PERPS_DEPOSIT / PERPS_WITHDRAW） |
| confirm_set_tpsl | 止盈止损 |
| view_position | 查看仓位 |

# Anti-Patterns

- **不要**在参数不全时调用 tool，先追问用户
- **不要**在 `interact_mode=frontend` 下直接执行真实交易，只生成 confirm card
- **不要**跳过参数验证直接调用 tool

# Resources

- [confirm_perp_open_order 参数详解](resources/confirm_perp_open_order.md)
- [confirm_perp_close_position 参数详解](resources/confirm_perp_close_position.md)
- [confirm_perp_transfer 参数详解](resources/confirm_perp_transfer.md)
- [confirm_set_tpsl 参数详解](resources/confirm_set_tpsl.md)
