# confirm_perp_close_position 参数详解

## 概述

平仓 action，生成 CLOSE_POSITION 的 confirm card。支持单个或**批量**平仓（与开仓不同，平仓可以一次处理多个 coin）。

## 参数表

| 参数 | 类型 | 说明 |
|------|------|------|
| closes | list[CloseItem] | 平仓项列表，支持批量 |
| source_text | str | 用户原始表达，不影响逻辑 |

### CloseItem 子对象

| 子参数 | 类型 | 说明 |
|--------|------|------|
| coin | str | 币种名称，如 "BTC"、"ETH" |
| position_side | Literal["long", "short"] | 仓位方向 |
| position_size | float | 当前仓位大小（合约数量） |
| close_size | float \| None | 本次平仓数量（不填则全平） |
| close_ratio | float \| None | 本次平仓比例（0.5 = 平 50%），与 close_size 互斥 |
| mark_price | float \| None | 当前标记价格 |

## close_size / close_ratio 互斥规则

`close_size` 和 `close_ratio` 必须二选一，不能同时指定：

- 指定平仓数量 → 用 `close_size`，如 `close_size=0.5`（平 0.5 个）
- 指定平仓比例 → 用 `close_ratio`，如 `close_ratio=0.5`（平 50%）
- 两者都不指定 → 全平，`closeRatio = 1.0`

## execution_plan 输出字段

CLOSE_POSITION intent 字段说明：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `intent` | string | ✅ | 固定值 `"CLOSE_POSITION"` |
| `coin` | string | ✅ | 币种 |
| `size` | string | 二选一 | 平仓数量（全平时不填） |
| `closeRatio` | number | 二选一 | 平仓比例，`1`=全平，`0.5`=平一半 |
| `isLong` | boolean | ✅ | `true`=多头仓，`false`=空头仓 |
| `markPrice` | number \| null | ✅ | 当前标记价格 |

`size` 和 `closeRatio` 互斥，二选一返回。

## 使用示例

**全平单个仓位：**
```python
closes=[{
  "coin": "BTC",
  "position_side": "long",
  "position_size": 1.5,
  "mark_price": 68720.2
}]
source_text="把 BTC 仓位全平掉"
```

**平一半仓位：**
```python
closes=[{
  "coin": "ETH",
  "position_side": "short",
  "position_size": 1.0,
  "close_ratio": 0.5,
  "mark_price": 3650.0
}]
source_text="平掉一半 ETH 仓位"
```

**批量平仓（多个 coin 一次平）：**
```python
closes=[
  {"coin": "BTC", "position_side": "long", "position_size": 1.5, "close_ratio": 0.5, "mark_price": 68720.2},
  {"coin": "ETH", "position_side": "short", "position_size": 1.0, "mark_price": 3650.0}
]
source_text="把 BTC 平一半，ETH 全平"
```

**指定数量平仓：**
```python
closes=[{
  "coin": "BTC",
  "position_side": "long",
  "position_size": 1.5,
  "close_size": 0.5,
  "mark_price": 68720.2
}]
source_text="平 0.5 个 BTC"
```
