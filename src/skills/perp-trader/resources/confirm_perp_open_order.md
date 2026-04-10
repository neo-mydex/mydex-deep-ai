# confirm_perp_open_order

## 概述

开仓 action，生成 OPEN_LONG 或 OPEN_SHORT 的 confirm card。

## 参数表

| 参数 | 类型 | 说明 |
|------|------|------|
| coin | str | 币种名称，如 "BTC"、"ETH" |
| leverage | float | 杠杆倍数（必须用 check_can_open 返回的 leverage_to_use） |
| usdc_size | float | 投入的 USDC 数量，如 1000 表示 1000 USDC |
| side | Literal["long", "short"] | "long"=做多，"short"=做空 |
| is_add | bool | false=开新仓，true=补仓（由 check_can_open 推断） |
| margin_mode | Literal["cross", "isolated"] | 默认 "cross"（全仓） |
| order_type | Literal["market", "limit"] | 默认 "market"（市价） |
| entry_price | float \| None | 限价单入场价格（仅限价单需填） |
| tp | float \| None | 止盈价格，如 72000 |
| sl | float \| None | 止损价格，如 66500 |
| tp_ratio | float \| None | 止盈比例（0.3 = 30%），与 tp 互斥 |
| sl_ratio | float \| None | 止损比例（0.1 = 10%），与 sl 互斥 |
| mark_price | float \| None | 当前标记价格（用于计算仓位大小） |
| source_text | str | 用户原始表达，不影响逻辑 |

## is_add

- **`is_add=false`（默认）**：新开仓
  - `execution_plan` 包含两个 step：
    1. `UPDATE_LEVERAGE`：设置杠杆和全仓/逐仓
    2. `OPEN_ORDER`：下单

- **`is_add=true`**：补仓（往已有仓位追加保证金）
  - `execution_plan` 只有一个 step：
    1. `OPEN_ORDER`：追加保证金，不调杠杆（因为仓位已用同一杠杆）

## tp / tp_ratio 互斥规则

`tp` 和 `tp_ratio` 必须二选一，不能同时指定：

- 指定止盈价格 → 用 `tp`，如 `tp=72000`
- 指定止盈比例 → 用 `tp_ratio`，如 `tp_ratio=0.3`（30%）
- 两者都不指定 → 无止盈

## sl / sl_ratio 互斥规则

`sl` 和 `sl_ratio` 必须二选一，不能同时指定：

- 指定止损价格 → 用 `sl`，如 `sl=66500`
- 指定止损比例 → 用 `sl_ratio`，如 `sl_ratio=0.1`（10%）
- 两者都不指定 → 无止损

## 仓位大小计算

`mark_price` 用于计算合约数量 `size`：

```
size = usdc_size * leverage / mark_price
```

例如：`usdc_size=1000, leverage=20, mark_price=68450.5`
→ `size = 1000 * 20 / 68450.5 ≈ 0.292182`

## 杠杆与全仓/逐仓

`UPDATE_LEVERAGE` step 中的 `isCross` 含义：
- `isCross=true`：`margin_mode="cross"`（全仓）
- `isCross=false`：`margin_mode="isolated"`（逐仓）

## 使用示例

**新开多仓：**
```
coin="BTC", leverage=20, usdc_size=1000,
tp=72000, sl=66500, mark_price=68450.5
```

**新开空仓（限价）：**
```
coin="ETH", leverage=10, usdc_size=500,
order_type="limit", entry_price=3650,
tp=3450, sl=3720, mark_price=3650
```

**补仓：**
```
is_add=true, coin="BTC", leverage=10, usdc_size=100, mark_price=71000
```

**用比例止盈止损：**
```
coin="BTC", leverage=10, usdc_size=1000,
tp_ratio=0.3, sl_ratio=0.1, mark_price=68000
```
