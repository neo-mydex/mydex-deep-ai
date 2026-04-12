# confirm_perp_cancel_open_orders

## 概述

取消挂单 action，生成 CANCEL_OPEN_ORDER 的 confirm card。

## 参数表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| coin | str | 是 | 币种名称，如 "BTC"、"ETH" |
| order_type | str | 否 | 订单类型，"limit" / "market" / "tp" / "sl"，不传则不限类型 |
| source_text | str | 否 | 用户原始表达 |

## 返回字段

| 字段 | 类型 | 说明 |
|------|------|------|
| action | str | 固定 "CANCEL_OPEN_ORDER" |
| execution_plan | list | 包含 CANCEL_OPEN_ORDER intent |
| meta.source_text | str | 用户原始表达 |

## CANCEL_OPEN_ORDER intent 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| intent | str | 固定 "CANCEL_OPEN_ORDER" |
| oid | str | 订单 ID |
| coin | str | 币种 |
| direction | str | "long" 或 "short" |
| leverage | int | 杠杆倍数 |
| type | str | "limit" / "market" / "tp" / "sl" |
| limitPrice | str | 限价价格 |
| tpPrice | str | 止盈触发价格 |
| slPrice | str | 止损触发价格 |
| size | str | 订单数量 |
| usdcSize | str | 仓位价值 |
| unrealizedPnl | str | 未实现盈亏 |
| entryPrice | str | 入场价格 |
| timestamp | int | 订单创建时间戳 |

## 工作流

1. 调用 `perp_get_open_orders` 获取用户挂单列表
2. 根据 coin 和 order_type 筛选匹配的订单
3. 若匹配到多个 → agent 追问用户要取消哪个
4. 若匹配到1个 → 调用 `confirm_perp_cancel_open_orders(coin=xxx, order_type=yyy)` 生成取消卡片

## 使用示例

```
confirm_perp_cancel_open_orders(
  coin="BTC",
  order_type="limit",
  source_text="取消 BTC 限价单",
)
```

## 注意事项

- **自动筛选**：根据 coin 和 order_type 自动查找匹配的订单
- **多个匹配**：如果找到多个匹配的订单，raise ValueError 让 agent 追问用户
- **无匹配**：如果没有匹配的订单，raise ValueError("没有找到 {coin} 的 {type} 挂单")
- **批量取消**：每轮可取消多个订单，每个订单一个 CANCEL_OPEN_ORDER intent
