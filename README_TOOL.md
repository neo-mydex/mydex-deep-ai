# Tools 命令行使用指南

本文件介绍如何从项目根目录通过命令行运行各个 Tool 函数，方便测试和调试。

## 运行格式

```bash
uv run python -m src.tools.<模块名> [参数]
```

> **注意**：首次运行可能出现 `RuntimeWarning: ... found in sys.modules after import of package ...` 警告，这是 Python 使用 `-m` 运行 submodule 的正常现象，不影响功能，可以忽略。

---

## perp 模块（永续合约查询）

### 1. get_market - 市场数据查询

```bash
uv run python -m src.tools.perp.get_market --action <action> [可选参数]
```

**参数说明**：

| 参数 | 必填 | 说明 | 可选值 |
|------|------|------|--------|
| `--action` | 是 | 查询类型 | `price`, `coin_info`, `all_mids` |
| `--coin` | 否 | 币种符号，默认 BTC | 如 `BTC`, `ETH`, `SOL` |
| `--network` | 否 | 网络，默认 mainnet | `mainnet`, `testnet` |
| `--timeout` | 否 | 超时时间，默认 10s | 浮点数 |

**action 说明**：
- `price` - 查询币种当前市场价格
- `coin_info` - 查询币种详细信息（是否上市、最大杠杆等）
- `all_mids` - 查询所有币种的中间价

**示例**：
```bash
# 查询 BTC 当前价格
uv run python -m src.tools.perp.get_market --action price --coin BTC

# 查询 ETH 是否上市及最大杠杆
uv run python -m src.tools.perp.get_market --action coin_info --coin ETH

# 查询所有币种中间价
uv run python -m src.tools.perp.get_market --action all_mids
```

**输出示例**（`price`）：
```json
{
  "ok": true,
  "network": "mainnet",
  "coin": "BTC",
  "mark_price": 67500.0,
  "mark_price_raw": "67500.0",
  "is_listed": true
}
```

**输出字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ok` | bool | 查询是否成功 |
| `network` | string | 网络名称 |
| `coin` | string | 币种符号 |
| `mark_price` | float | 市场标记价格 |
| `mark_price_raw` | string | 原始价格字符串 |
| `is_listed` | bool | 是否上市 |

---

### 2. get_positions - 仓位查询

```bash
uv run python -m src.tools.perp.get_positions --action <action> --address <地址> [可选参数]
```

**参数说明**：

| 参数 | 必填 | 说明 | 可选值 |
|------|------|------|--------|
| `--action` | 是 | 查询类型 | `all`, `one` |
| `--address` | 是 | 钱包地址 | 0x 开头地址 |
| `--coin` | 否 | 币种，默认 BTC | 如 `BTC`, `ETH` |
| `--network` | 否 | 网络，默认 mainnet | `mainnet`, `testnet` |
| `--dex` | 否 | DEX 标识 | 空字符串 |
| `--timeout` | 否 | 超时时间，默认 10s | 浮点数 |

**action 说明**：
- `all` - 查询所有仓位
- `one` - 查询指定币种仓位

**示例**：
```bash
# 查询钱包所有仓位
uv run python -m src.tools.perp.get_positions --action all --address 0x802f71cBf691D4623374E8ec37e32e26d5f74d87

# 查询 ETH 仓位
uv run python -m src.tools.perp.get_positions --action one --address 0x802f71cBf691D4623374E8ec37e32e26d5f74d87 --coin ETH
```

**输出示例**（`one`）：
```json
{
  "ok": true,
  "address": "0x802f71cBf691D4623374E8ec37e32e26d5f74d87",
  "coin": "ETH",
  "network": "mainnet",
  "has_position": true,
  "position_side": "long",
  "position_size": 1.5,
  "entry_px": 3500.0,
  "mark_px": 3650.0,
  "leverage": 10,
  "margin_type": "cross",
  "liquidation_px": 3200.0,
  "unrealized_pnl": 225.0
}
```

**输出字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ok` | bool | 查询是否成功 |
| `address` | string | 钱包地址 |
| `coin` | string | 币种符号 |
| `network` | string | 网络名称 |
| `has_position` | bool | 是否有仓位 |
| `position_side` | string | 持仓方向：`long` 多 / `short` 空 / `flat` 无 |
| `position_size` | float | 持仓数量 |
| `entry_px` | float | 开仓均价 |
| `mark_px` | float | 标记价格（当前价） |
| `leverage` | int | 杠杆倍数 |
| `margin_type` | string | 保证金模式：`cross` 全仓 / `isolated` 逐仓 |
| `liquidation_px` | float | 强平价格 |
| `unrealized_pnl` | float | 未实现盈亏 |

---

### 3. get_user_state - 用户状态查询

```bash
uv run python -m src.tools.perp.get_user_state --action <action> --address <地址> [可选参数]
```

**参数说明**：

| 参数 | 必填 | 说明 | 可选值 |
|------|------|------|--------|
| `--action` | 是 | 查询类型 | `balance`, `state` |
| `--address` | 是 | 钱包地址 | 0x 开头地址 |
| `--network` | 否 | 网络，默认 mainnet | `mainnet`, `testnet` |
| `--dex` | 否 | DEX 标识 | 空字符串 |
| `--timeout` | 否 | 超时时间，默认 10s | 浮点数 |

**action 说明**：
- `balance` - 查询账户余额（标准化返回）
- `state` - 查询账户原始状态

**示例**：
```bash
# 查询账户余额
uv run python -m src.tools.perp.get_user_state --action balance --address 0x802f71cBf691D4623374E8ec37e32e26d5f74d87
```

**输出示例**（`balance`）：
```json
{
  "ok": true,
  "address": "0x802f71cBf691D4623374E8ec37e32e26d5f74d87",
  "network": "mainnet",
  "withdrawable": 1000.0,
  "account_value": 5000.0,
  "total_margin_used": 500.0
}
```

**输出字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ok` | bool | 查询是否成功 |
| `address` | string | 钱包地址 |
| `network` | string | 网络名称 |
| `withdrawable` | float | 可提取余额 |
| `account_value` | float | 账户总价值 |
| `total_margin_used` | float | 已用保证金 |

---

### 4. get_open_orders - 挂单查询

```bash
uv run python -m src.tools.perp.get_open_orders --address <地址> [可选参数]
```

**参数说明**：

| 参数 | 必填 | 说明 | 可选值 |
|------|------|------|--------|
| `--address` | 是 | 钱包地址 | 0x 开头地址 |
| `--coin` | 否 | 币种，不传则查所有 | 如 `BTC`, `ETH` |
| `--network` | 否 | 网络，默认 mainnet | `mainnet`, `testnet` |
| `--dex` | 否 | DEX 标识 | 空字符串 |
| `--timeout` | 否 | 超时时间，默认 10s | 浮点数 |

**示例**：
```bash
# 查询所有挂单
uv run python -m src.tools.perp.get_open_orders --address 0x802f71cBf691D4623374E8ec37e32e26d5f74d87

# 查询 BTC 挂单
uv run python -m src.tools.perp.get_open_orders --address 0x802f71cBf691D4623374E8ec37e32e26d5f74d87 --coin BTC
```

**输出示例**：
```json
{
  "ok": true,
  "address": "0x802f71cBf691D4623374E8ec37e32e26d5f74d87",
  "network": "mainnet",
  "coin": null,
  "has_open_orders": true,
  "open_order_count": 2,
  "has_tpsl_orders": true,
  "tpsl_order_count": 1,
  "orders": [...]
}
```

**输出字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ok` | bool | 查询是否成功 |
| `address` | string | 钱包地址 |
| `network` | string | 网络名称 |
| `coin` | string/null | 查询的币种，null 表示全部 |
| `has_open_orders` | bool | 是否有挂单 |
| `open_order_count` | int | 挂单数量 |
| `has_tpsl_orders` | bool | 是否有止盈止损挂单 |
| `tpsl_order_count` | int | 止盈止损挂单数量 |
| `orders` | array | 订单列表 |

---

## coin 模块（代币信息）

### coingecko - 代币价格和信息

```bash
uv run python -m src.tools.coin.coingecko --action <action> --coin <币种> [可选参数]
```

**参数说明**：

| 参数 | 必填 | 说明 | 可选值 |
|------|------|------|--------|
| `--action` | 是 | 查询类型 | `price`, `info`, `search`, `trending` |
| `--coin` | 否 | 代币符号、名称或合约地址（支持模糊搜索） | 如 `BTC`, `bitcoin`, `solana` |
| `--vs` | 否 | 计价货币，默认 usd | `usd`, `cny`, `eur` |

**action 说明**：
- `price` - 查询代币当前价格
- `info` - 查询代币详细信息（包含市值、排名等）
- `search` - 搜索代币，返回候选列表
- `trending` - 查询 trending 代币

**`--coin` 支持的输入类型**：
- **符号**：如 `BTC`, `ETH`, `SOL`
- **名称**：如 `bitcoin`, `ethereum`, `solana`（支持模糊搜索）
- **合约地址**：如 `0x6982508145454Ce325dDbE47a25d4ec3d2311933`（自动尝试 eth/base/arb/op 等网络）

**示例**：
```bash
# 查询 BTC 价格（符号）
uv run python -m src.tools.coin.coingecko --action price --coin BTC

# 查询 ETH 详情（符号）
uv run python -m src.tools.coin.coingecko --action info --coin ETH

# 查询 solana 详情（名称模糊搜索 → 匹配到 Solana）
uv run python -m src.tools.coin.coingecko --action info --coin solana

# 通过合约地址查询 PEPE
uv run python -m src.tools.coin.coingecko --action info --coin 0x6982508145454Ce325dDbE47a25d4ec3d2311933

# 搜索代币
uv run python -m src.tools.coin.coingecko --action search --coin solana

# 查询 trending 代币
uv run python -m src.tools.coin.coingecko --action trending
```

**输出示例**（`price`）：
```json
{
  "ok": true,
  "coin": "BTC",
  "coin_id": "bitcoin",
  "vs": "usd",
  "price": 71298.0,
  "change_24h": 4.47,
  "source": "coingecko"
}
```

**输出示例**（`info`）：
```json
{
  "ok": true,
  "coin": "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
  "coin_id": "pepe",
  "name": "Pepe",
  "symbol": "PEPE",
  "price": 3.46e-06,
  "change_24h": 4.74,
  "market_cap": 1455543942,
  "rank": 54,
  "contract_address": "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
  "networks": {
    "ethereum": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
    "avalanche": "0xa659d083b677d6bffe1cb704e1473b896727be6d"
  },
  "source": "coingecko"
}
```

**输出示例**（`search`）：
```json
{
  "ok": true,
  "query": "solana",
  "candidates": [
    {
      "id": "solana",
      "name": "Solana",
      "symbol": "SOL",
      "rank": 7,
      "platforms": {}
    },
    {
      "id": "solana-the-pygmy-hippo",
      "name": "Solana The Pygmy Hippo",
      "symbol": "SOLANA",
      "rank": 6873,
      "platforms": {
        "solana": "De4ULouuU2cAQkhKuYrsrFtJGRRmcSwQD5esmnAUpump"
      }
    }
  ],
  "source": "coingecko"
}
```

**输出字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ok` | bool | 查询是否成功 |
| `coin` | string | 查询的币种（输入原值） |
| `coin_id` | string | CoinGecko ID |
| `name` | string | 代币全称 |
| `symbol` | string | 代币符号 |
| `price` | float | 当前价格 |
| `change_24h` | float | 24 小时涨跌幅 (%) |
| `market_cap` | float | 市值 |
| `rank` | int | 市值排名 |
| `contract_address` | string | 合约地址（输入为合约地址时） |
| `networks` | object | 该代币在各链的合约地址映射 |
| `source` | string | 数据来源 |

**环境变量**：

| 变量 | 说明 |
|------|------|
| `COINGECKO_PRO_API_KEY` | CoinGecko Pro API 密钥（有付费密钥时自动使用 pro 接口） |

---

## user 模块（用户相关）

### decode_jwt - JWT 解析

```bash
uv run python -m src.tools.user.decode_jwt
```

**说明**：解码 Privy JWT token，提取用户信息。CLI 需要 token 参数时直接从 stdin 读取。

**函数导入**：
```python
from src.tools.user import get_userid, get_jwt_expired_time, get_userid_and_expired_time
```

**返回结构**：
```python
{
    "user_id": "did:privy:cmmsl6t2402020cl2rperc5m1",
    "expire_at_utc": "2026-03-25T03:46:52+00:00",
    "is_expired": False,
}
```

---

### get_onchain_assets - 链上资产查询

```bash
uv run python -m src.tools.user.get_onchain_assets --address <地址> [可选参数]
```

**参数说明**：

| 参数 | 必填 | 说明 | 可选值 |
|------|------|------|--------|
| `--address` | 是 | 钱包地址 | 0x 开头地址 |
| `--networks` | 否 | 网络列表，默认 eth,base,arb,op | 如 `eth,base,arb` |
| `--min-value` | 否 | 最小 USD 值过滤，默认 0.01 | 浮点数 |

**示例**：
```bash
# 查询 ETH 和 Base 网络资产
uv run python -m src.tools.user.get_onchain_assets --address 0x802f71cBf691D4623374E8ec37e32e26d5f74d87 --networks eth,base

# 查询所有支持网络
uv run python -m src.tools.user.get_onchain_assets --address 0x802f71cBf691D4623374E8ec37e32e26d5f74d87
```

**输出示例**：
```json
{
  "ok": true,
  "address": "0x802f71cBf691D4623374E8ec37e32e26d5f74d87",
  "networks": ["eth-mainnet", "base-mainnet"],
  "total_value_usd": 15234.56,
  "asset_count": 5,
  "assets": [
    {
      "network": "eth-mainnet",
      "symbol": "ETH",
      "balance": 2.5,
      "value_usd": 5000.0,
      "is_native": true
    }
  ],
  "breakdown": {
    "eth-mainnet": {
      "total_value_usd": 10000.0,
      "asset_count": 3
    }
  }
}
```

**输出字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ok` | bool | 查询是否成功 |
| `address` | string | 钱包地址 |
| `networks` | array | 查询的网络列表 |
| `total_value_usd` | float | 总资产 USD 值 |
| `asset_count` | int | 资产数量 |
| `assets` | array | 资产列表 |
| `breakdown` | object | 按网络汇总 |

**环境变量**：

| 变量 | 说明 |
|------|------|
| `ALCHEMY_API_KEY` | Alchemy API 密钥（用于查询链上资产） |

---

## card 模块（交易 Action Card）

card 模块不通过命令行运行，而是作为 Python 模块被 Agent 调用，构建交易参数。

详见 `src/tools/card/` 目录下的各个 `action_*.py` 文件。

### 模块导入方式

```python
from src.tools.card import (
    build_open_long_params,
    build_open_short_params,
    action_open_position,
    build_close_position_params,
    action_close_position,
    # ...
)
```

### Action Card 类型

| Card | 说明 | 关键参数 |
|------|------|----------|
| `OPEN_LONG` | 开多 | `coin`, `usdc_size`, `leverage`, `tp/sl` |
| `OPEN_SHORT` | 开空 | `coin`, `usdc_size`, `leverage`, `tp/sl` |
| `CLOSE_POSITION` | 平仓 | `coin`, `close_mode` |
| `SET_TPSL` | 设置止盈止损 | `coin`, `tp`, `sl` |
| `UPDATE_LEVERAGE` | 更新杠杆 | `coin`, `leverage`, `margin_mode` |
| `VIEW_POSITION` | 查看仓位 | `coin`, `include_open_orders` |
