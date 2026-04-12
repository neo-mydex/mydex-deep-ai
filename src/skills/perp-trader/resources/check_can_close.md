# perp_check_can_close

## 概述

平仓前可行性检查。在实际平仓前，验证以下条件：

- 是否有仓位可以平
- 是否有未撤销的主单（不含 TPSL 触发单）
- 市场价格是否可用
- 平仓数量是否有效
- 仓位是否接近强平价格（correction 警告，不 block）

## 三选一输入模式

| 参数 | 说明 | 示例 |
|------|------|------|
| close_size | 币本位张数 | 0.5 BTC |
| close_size_in_usdc | USDC 价值 | 34000 USDC |
| close_ratio | 0-1 比例 | 0.3 = 平 30% |

⚠️ 三者**只能指定其一**，不可同时传入。

## 参数表

| 参数 | 类型 | 说明 |
|------|------|------|
| address | str | 用户钱包地址 |
| coin | str \| None | 币种名称，如 "BTC"、"ETH"，不传则返回所有仓位（批量模式） |
| close_size | float \| None | 平仓数量（币本位） |
| close_size_in_usdc | float \| None | 平仓价值（USDC） |
| close_ratio | float \| None | 平仓比例（0-1） |
| network | str | 网络类型，"mainnet" 或 "testnet" |

## 返回字段

| 字段 | 类型 | 说明 |
|------|------|------|
| ok | bool | 所有检查是否通过 |
| matching_positions | list[MatchingPosition] | 仓位列表，每个元素对应一个 coin |
| corrections | list[str] | 警告/纠正信息（非 block） |
| issues | list[dict] | 问题列表（block） |
| follow_up_question | str | 给用户的后续问题 |

### MatchingPosition 子对象

| 子参数 | 类型 | 说明 |
|--------|------|------|
| coin | str | 币种名称 |
| side | "long" \| "short" | 仓位方向 |
| size | float | 当前持仓量（币本位） |
| close_ratio | float \| None | 本次平仓比例 |
| close_size | float \| None | 本次平仓量（币本位） |
| mark_price | float \| None | 当前标记价格 |

## issues code 说明（block）

| code | 说明 |
|------|------|
| `query_failed` | 查询仓位失败 |
| `price_unavailable` | 无法获取市场价格 |
| `no_position` | 没有仓位，无需平仓 |
| `invalid_input` | 参数无效（如批量模式使用 close_size） |
| `has_open_orders` | 有未撤销主单，需先撤销 |
| `invalid_close_size` | 平仓数量 <= 0 |

## corrections 说明（非 block）

| 消息 | 说明 |
|------|------|
| "平仓量 X > 持仓量 Y，已裁剪为全平" | 自动裁剪超量 |
| "仓位接近强平价格，距离 N%，请留意" | 强平风险警告 |
| "close_ratio 已自动纠正为 1.0..." | 输入超出范围，自动纠正 |

## 使用示例

**指定张数平仓：**
```
perp_check_can_close(address="0x...", coin="BTC", close_size=0.5)
```

**指定 USDC 价值平仓：**
```
perp_check_can_close(address="0x...", coin="BTC", close_size_in_usdc=5000)
```

**指定比例平仓：**
```
perp_check_can_close(address="0x...", coin="BTC", close_ratio=0.3)
# 平 30% 的仓位
```

**批量平所有仓位一半（coin=None）：**
```
perp_check_can_close(address="0x...", coin=None, close_ratio=0.5)
# 返回所有有仓位的 coin，各自平 50%
```
