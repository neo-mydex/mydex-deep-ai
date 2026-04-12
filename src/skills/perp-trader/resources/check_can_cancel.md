# check_can_cancel

## 概述

取消挂单前可行性检查，校验用户是否有符合条件的挂单可以取消。

## 参数表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| address | str | 是 | 用户钱包地址 |
| coin | str | 否 | 币种名称，如 "BTC"、"ETH" |
| order_type | str | 否 | 订单类型，"limit" / "market" / "tp" / "sl" |
| network | str | 否 | "mainnet" 或 "testnet"，默认 "mainnet" |

## 返回字段

| 字段 | 类型 | 说明 |
|------|------|------|
| ok | bool | 是否有可取消的订单 |
| matching_orders | list[MatchingOrder] | 匹配的订单列表 |
| corrections | list[str] | 警告/纠正 |
| issues | list[dict] | 问题列表 |
| follow_up_question | str | 后续问题 |

### MatchingOrder 子对象

| 子参数 | 类型 | 说明 |
|--------|------|------|
| oid | int | 订单 ID |
| coin | str | 币种名称 |
| size | float | 订单数量 |
| type | "limit" \| "market" \| "tp" \| "sl" | 订单类型 |
| side | "long" \| "short" | 方向（B→long, S→short） |
| limit_price | float \| null | 限价（limit 单） |
| trigger_price | float \| null | 触发价（tp/sl 单） |
| timestamp | int | 下单时间戳 |
| reduce_only | bool | 是否只减仓 |

## 工作流

1. 调用 `perp_check_can_cancel(address, coin=xxx, order_type=yyy)`
2. 若 `ok=true` → 调用 `confirm_perp_cancel_open_orders(coin=xxx, order_type=yyy)`
3. 若 `ok=false` → 告知用户"没有找到符合条件的挂单"

## 使用示例

**检查 BTC 限价单：**
```
perp_check_can_cancel(
  address="0x...",
  coin="BTC",
  order_type="limit",
)
```

**检查所有挂单：**
```
perp_check_can_cancel(address="0x...")
```
