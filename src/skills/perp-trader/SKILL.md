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
| 止盈，止损，设置 tpsl | set_tpsl | 止盈止损 |
| 仓位，持仓，当前 | view_position | 查看仓位 |

# SOP（4 步）

## 第一步：识别意图

根据用户输入，匹配上方 Intent Routing Table，选定对应 Tool。

## 第二步：收集参数

根据意图类型，参考对应 resource 文件获取详细参数说明：

- 开仓 → [confirm_perp_open_order 参数详解](resources/open-position.md)
- 平仓 → confirm_perp_close_position（待补充）
- 划转 → [confirm_perp_transfer 参数详解](resources/transfer.md)
- 止盈止损 → set_tpsl（待补充）
- 查看仓位 → 参数仅需 coin

**参数不全时**：主动追问用户，不自行查询。

## 第三步：验证参数合理性

调用 tool 前，验证关键约束：

- tp 和 tp_ratio 互斥（二选一）
- sl 和 sl_ratio 互斥（二选一）
- leverage 必须 > 0
- usdc_size 必须 > 0
- coin 必须是有效币种

**验证失败**：直接告知用户问题所在，不调用 tool。

## 第四步：生成 Confirm Card

验证通过后，调用对应 action tool，返回 confirm card 等待用户确认。

# Tools

| Tool | 用途 |
|------|------|
| confirm_perp_open_order | 开仓（做多/做空） |
| confirm_perp_close_position | 平仓（待补充） |
| confirm_perp_transfer | 资金划转（PERPS_DEPOSIT / PERPS_WITHDRAW） |
| set_tpsl | 止盈止损（待补充） |
| view_position | 查看仓位 |

# Anti-Patterns

- **不要**在参数不全时调用 tool，先追问用户
- **不要**在 `interact_mode=frontend` 下直接执行真实交易，只生成 confirm card
- **不要**跳过参数验证直接调用 tool

# Resources

- [开仓参数详解](resources/open-position.md)
- [划转参数详解](resources/transfer.md)
