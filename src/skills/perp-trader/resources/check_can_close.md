# perp_check_can_close

## 概述

平仓前可行性检查。在实际平仓前，验证以下条件：

- 是否有仓位可以平
- 是否有未撤销的主单（不含 TPSL 触发单）
- 市场价格是否可用
- 平仓数量是否有效
- 仓位是否接近强平价格（correction 警告，不 block）

## 与 check_can_open 的类比

| | check_can_open | check_can_close |
|---|---|---|
| 前置于 | confirm_perp_open_order | confirm_perp_close_position |
| 检查重点 | 余额、杠杆、TP/SL 挂单 | 仓位、主单挂单、强平距离 |

## 参数表

| 参数 | 类型 | 说明 |
|------|------|------|
| address | str | 用户钱包地址 |
| coin | str | 币种名称，如 "BTC"、"ETH" |
| close_size | float \| None | 平仓数量（不传则全部平仓） |
| network | str | 网络类型，"mainnet" 或 "testnet" |

## 返回字段

| 字段 | 类型 | 说明 |
|------|------|------|
| ok | bool | 所有检查是否通过（issues 为空） |
| issues | list[dict] | 问题列表，为空则可继续 |
| follow_up_question | str | 给用户的后续问题 |
| corrections | list[str] | 警告信息（如强平距离），不 block |
| checks.position | dict | 仓位查询结果 |
| checks.open_orders | dict | 挂单查询结果 |
| checks.market | dict | 市场价格查询结果 |
| position_info.has_position | bool | 是否有仓位 |
| position_info.position_side | Literal["long", "short", "flat"] | 仓位方向 |
| position_info.position_size | float \| None | 仓位大小 |
| position_info.close_size | float | 实际平仓数量 |

## issues code 说明

| code | 说明 | 是否 block |
|------|------|------------|
| `query_failed` | 查询仓位失败 | ✅ |
| `price_unavailable` | 无法获取市场价格 | ✅ |
| `no_position` | 没有仓位，无需平仓 | ✅ |
| `has_open_orders` | 有未撤销主单，需先撤销 | ✅ |
| `invalid_close_size` | 平仓数量无效 | ✅ |

## corrections 说明（非 block）

| 消息 | 说明 |
|------|------|
| "平仓量 X > 持仓量 Y，已裁剪为全平" | 自动裁剪超量 |
| "仓位接近强平价格，距离 N%，请留意" | 强平风险警告 |

## 使用示例

**全部平仓前检查：**
```python
perp_check_can_close(address="0x...", coin="BTC")
# 若 ok=true，调用 confirm_perp_close_position
```

**部分平仓前检查：**
```python
perp_check_can_close(address="0x...", coin="BTC", close_size=0.5)
# 若 ok=true，用返回的 close_size 调用 confirm_perp_close_position
```
