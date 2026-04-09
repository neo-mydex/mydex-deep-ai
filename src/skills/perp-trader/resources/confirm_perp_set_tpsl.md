# confirm_perp_set_tpsl

## 概述

止盈止损 action，生成 SET_TPSL 的 confirm card。不允许批量，每个 coin 单独设置。

## 参数表

| 参数 | 类型 | 说明 |
|------|------|------|
| coin | str | 币种名称，如 "BTC"、"ETH" |
| position_size | float | 当前仓位大小（合约数量） |
| tp_price | float \| None | 止盈价格，如 72000 |
| tp_ratio | float \| None | 止盈比例（0.3 = 30%），与 tp_price 互斥 |
| sl_price | float \| None | 止损价格，如 66500 |
| sl_ratio | float \| None | 止损比例（0.1 = 10%），与 sl_price 互斥 |
| existing_tp_oid | int | 0=第一次设置，非0=更新已有止盈单号 |
| existing_sl_oid | int | 0=第一次设置，非0=更新已有止损单号 |
| source_text | str | 用户原始表达，不影响逻辑 |

## tp_price / tp_ratio 互斥规则

`tp_price` 和 `tp_ratio` 必须二选一，不能同时指定：

- 指定止盈价格 → 用 `tp_price`，如 `tp_price=72000`
- 指定止盈比例 → 用 `tp_ratio`，如 `tp_ratio=0.3`（30%）

## sl_price / sl_ratio 互斥规则

`sl_price` 和 `sl_ratio` 必须二选一，不能同时指定：

- 指定止损价格 → 用 `sl_price`，如 `sl_price=66500`
- 指定止损比例 → 用 `sl_ratio`，如 `sl_ratio=0.1`（10%）

## existing_tp_oid / existing_sl_oid

- **0**：该方向第一次设置 TPSL
- **非0**：更新已有 TPSL 订单，传入原订单号

## 使用示例

**价格止盈止损：**
```
coin="BTC", position_size=0.2921,
tp_price=72000, sl_price=66500,
source_text="BTC 仓位止盈 72000，止损 66500"
```

**只设止盈（不设止损）：**
```
coin="BTC", position_size=0.2921,
tp_price=72000,
source_text="BTC 仓位止盈 72000"
```

**比例止盈止损：**
```
coin="ETH", position_size=1.0,
tp_ratio=0.3, sl_ratio=0.1,
source_text="ETH 仓位 30% 止盈，10% 止损"
```

**更新已有 TPSL：**
```
coin="BTC", position_size=0.2921,
tp_price=72500, existing_tp_oid=18273645,
existing_sl_oid=0,
source_text="把 BTC 止盈改成 72500"
```
