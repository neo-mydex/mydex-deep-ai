# perp_check_can_open

## 概述

开仓前可行性校验工具，在调用 `confirm_perp_open_order` 之前必须先通过此检查。

## 双输入模式

| 参数 | 说明 | 示例 |
|------|------|------|
| usdc_margin | USDC 保证金（投入多少 USDC） | 1000 = 投入 1000 USDC |
| coin_size | 币本位头寸（想要多少张合约） | 0.1 BTC |

⚠️ `usdc_margin` 和 `coin_size` **二选一**，不可同时指定。

## 参数表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| address | str | 是 | 用户钱包地址 |
| coin | str | 是 | 币种名称，如 "BTC"、"ETH" |
| side | str | 是 | "long" 或 "short" |
| usdc_margin | float \| None | 否 | USDC 保证金，与 coin_size 二选一 |
| coin_size | float \| None | 否 | 币本位头寸，与 usdc_margin 二选一 |
| leverage | float | 是 | 杠杆倍数，如 10、20 |
| order_type | str | 否 | "market" 或 "limit"，默认 "market" |
| entry_price | float \| None | 否 | 限价单入场价格 |
| network | str | 否 | "mainnet" 或 "testnet"，默认 "mainnet" |

## 返回字段

| 字段 | 类型 | 说明 |
|------|------|------|
| ok | bool | 所有检查是否通过 |
| is_add | bool | true=补仓（加仓），false=开新仓 |
| leverage_to_use | float | 实际应使用的杠杆（杠杆纠正后） |
| coin_size | float \| None | 实际下单的合约张数（币本位） |
| usdc_margin | float \| None | 实际使用的保证金 |
| corrections | list[str] | 自动纠正/警告信息（非 block） |
| issues | list[dict] | 问题列表（block） |
| follow_up_question | str | 追问用户的问题 |

## corrections 说明（非 block）

| 消息 | 说明 |
|------|------|
| "杠杆已从 X 降为 Y" | 杠杆超限，自动纠正 |
| "杠杆已纠正为 Xx（与已有仓位一致）" | 补仓时杠杆必须与已有仓位一致 |
| "限价偏差 X%，请确认" | 限价偏离市场价 |

## issues.code 说明（block）

| code | 说明 |
|------|------|
| no_balance | 账户可用余额不足 |
| opposite_position_exists | 已有反向仓位，需先平仓 |
| coin_not_listed | 币种不在永续合约列表 |
| has_main_orders | 有未成交主单（TPSL 除外） |
| limit_price_far | 限价偏离市场价超过 3% |

## 使用示例

**做多 BTC 20x 1000u（已知无仓）：**
```
perp_check_can_open(
  address="0x...",
  coin="BTC",
  side="long",
  usdc_margin=1000,
  leverage=20,
)
// 返回 ok=true, is_add=false
// 调用 confirm_perp_open_order(leverage=20, usdc_size=1000, ...)
```

**做多 BTC 10x 0.1 BTC（已知有同向仓位）：**
```
perp_check_can_open(
  address="0x...",
  coin="BTC",
  side="long",
  coin_size=0.1,
  leverage=10,
)
// 返回 ok=true, is_add=true, leverage_to_use=已有仓位杠杆
// corrections: ["杠杆已纠正为 Xx（与已有仓位一致）"]
// 调用 confirm_perp_open_order(leverage=X, is_add=true, ...)
```
