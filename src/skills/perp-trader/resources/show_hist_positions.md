# show_hist_positions

## 概述

查看历史仓位 action，生成 VIEW_HIST_POSITION 的 confirm card。不允许批量，每个 coin 单独设置。

## 参数表

| 参数 | 类型 | 说明 |
|------|------|------|
| address | str | 用户钱包地址 |
| coin | str \| None | 币种名称，如 "BTC"，不传则查所有 |
| start_time | int \| None | 开始时间（毫秒时间戳），默认最近 30 天 |
| end_time | int \| None | 结束时间（毫秒时间戳），默认当前 |
| source_text | str \| None | 用户原始表达，可选，默认为空字符串 |

## execution_plan 字段说明

每条记录对应一次历史成交。

| 字段 | 类型 | 说明 |
|------|------|------|
| intent | string | 固定 `"VIEW_HIST_POSITION"` |
| coin | string | 币种 |
| oid | string | 订单号 |
| unrealizedPnl | null | 历史成交不返回，固定 null |
| closedPnl | string \| null | 已平仓位盈亏（平仓成交有值，开仓成交则无） |
| entryPrice | string \| null | 开仓价格 |
| exitPrice | string \| null | 平仓价格 |
| timestamp | number | 成交时间戳（毫秒） |
| direction | string \| null | `"long"` 或 `"short"` |
| leverage | int \| null | 杠杆倍数 |
| type | string \| null | 订单类型：`"limit"`、`"tp"`、`"sl"` |
| limitPrice | string \| null | 限价 |
| tpPrice | string \| null | 止盈价 |
| slPrice | string \| null | 止损价 |
| size | string | 成交数量 |
| usdcSize | string | 成交价值（size × price） |

## direction 推断

| dir | side | direction |
|-----|------|-----------|
| open | Buy/B | long |
| open | Sell/S | short |
| close | Buy/B | short |
| close | Sell/S | long |
