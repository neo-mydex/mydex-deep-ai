# show_perp_open_order

## 概述

查看当前挂单（委托单）卡片，生成 VIEW_OPEN_ORDER 的 confirm card。

## 参数表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| address | str | 是 | 用户钱包地址 |
| coin | str | 否 | 币种名称，如 "BTC"、"ETH"，不传则返回所有挂单 |
| source_text | str | 否 | 用户原始表达 |

## 返回字段

| 字段 | 类型 | 说明 |
|------|------|------|
| action | str | 固定 "VIEW_OPEN_ORDER" |
| execution_plan | list | 包含 VIEW_OPEN_ORDER intent |
| meta.source_text | str | 用户原始表达 |

## VIEW_OPEN_ORDER intent 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| intent | str | 固定 "VIEW_OPEN_ORDER" |
| oid | str | 订单 ID |
| timestamp | int | 订单创建时间戳 |
| coin | str | 币种 |
| direction | str | "long" 或 "short" |
| leverage | int | 杠杆倍数 |
| type | str | "limit" / "market" / "tp" / "sl" |
| limitPrice | float | 限价价格 |
| tpPrice | float | 止盈触发价格 |
| slPrice | float | 止损触发价格 |
| size | str | 订单数量 |
| usdcSize | str | 仓位价值 |
| unrealizedPnl | str | 未实现盈亏 |
| entryPrice | str | 入场价格 |

## 工作流

1. 调用 `show_perp_open_order(address=xxx, coin=yyy)`
2. 若 coin 明确 → 只查该币的挂单
3. 若 coin 不明确 → 查所有挂单

## 使用示例

```
show_perp_open_order(
  address="0x...",
  coin="BTC",
  source_text="看看我 BTC 的挂单",
)
```

## 注意事项

- **按时间排序**：返回结果按 timestamp 倒序（新的在前）
- **direction 解析**：
  - reduceOnly=true 的订单：side=A→平多→"long"，side=B→平空→"short"
  - reduceOnly=false 的订单：side=B→开多→"long"，side=A→开空→"short"
- **仓位补充**：leverage、unrealizedPnl、entryPrice 等字段从对应仓位补充
