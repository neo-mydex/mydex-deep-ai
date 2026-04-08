# Tools 命令行使用指南

## 架构说明

项目分为两层：

| 层 | 路径 | 用途 | CLI 支持 |
|---|------|------|---------|
| **Tool** | `src/tools/` | 薄封装，`@tool` + Pydantic，给 Agent 用 | 无参数，硬编码默认值 |
| **Service** | `src/services/` | 实际业务逻辑，可被其他 API 调用 | argparse CLI，支持参数 |

`if __name__ == "__main__"` 在 tool 文件里用于冒烟测试（硬编码值），实际调试用 service CLI。

---

## Tool 层：冒烟测试

```bash
uv run python -m src.tools.<模块名>.<文件名>
```

> **注意**：首次运行可能出现 `RuntimeWarning`，可忽略或加 `PYTHONWARNINGS=ignore` 前缀。

### coin 模块

```bash
uv run python -m src.tools.coin.get_simple_price
uv run python -m src.tools.coin.get_detail_info
uv run python -m src.tools.coin.search_coins
uv run python -m src.tools.coin.get_trending_coins
```

**工具列表：**

| 工具 | 说明 |
|------|------|
| `coin_get_simple_price` | 轻量价格接口，返回价格 + 24h 变化 |
| `coin_get_detail_info` | 完整详情接口，返回价格、市值、排名、合约地址等 |
| `coin_search_coins` | 按关键词搜索代币候选 |
| `coin_get_trending_coins` | 查询热门代币 |

### perp 模块

```bash
uv run python -m src.tools.perp.get_market
uv run python -m src.tools.perp.get_positions
uv run python -m src.tools.perp.get_user_state
uv run python -m src.tools.perp.get_open_orders
uv run python -m src.tools.perp.check_can_open
uv run python -m src.tools.perp.check_can_close
```

### user 模块

```bash
uv run python -m src.tools.user.decode_jwt
uv run python -m src.tools.user.get_onchain_assets
```

**工具列表：**

| 工具 | 说明 |
|------|------|
| `user_get_userid` | 解析 JWT，返回 user_id + 过期时间 + 是否过期 |
| `user_get_wallet_address` | 调用后端 API，返回 EVM 和 Solana 钱包地址 |
| `wallet_get_assets` | 查询多链资产组合（仅 EVM 链） |
| `wallet_get_native_balance` | 查询原生代币余额（ETH、MATIC、SOL 等） |

> 注意：`wallet_get_assets` 仅支持 EVM 链（eth、base、arb、op、polygon、bnb、avax），不覆盖 Solana。

---

## Service 层：完整 CLI 调试

```bash
uv run python -m src.services.<模块名>.cli <子命令> [参数]
```

### CoinGecko Service

```bash
uv run python -m src.services.coingecko.cli --action price --coin BTC --vs usd
uv run python -m src.services.coingecko.cli --action info --coin BTC
uv run python -m src.services.coingecko.cli --action search --coin BTC
uv run python -m src.services.coingecko.cli --action trending
```

### Hyperliquid Service

```bash
uv run python -m src.services.hyperliquid.cli_main <子命令> [参数]
```

子命令：

| 子命令 | 说明 | 关键参数 |
|--------|------|---------|
| `get_market` | 市场数据 | `--action price\|coin_info\|perp_market_info --coin BTC` |
| `get_positions` | 仓位查询 | `--action all\|one --address 0x... --coin BTC` |
| `get_balance` | 账户余额 | `--address 0x... --network mainnet\|testnet` |
| `get_open_orders` | 挂单查询 | `--address 0x... --coin BTC` |

示例：

```bash
# 查询 BTC 市场价格
uv run python -m src.services.hyperliquid.cli_main get_market --action price --coin BTC

# 查询用户所有仓位
uv run python -m src.services.hyperliquid.cli_main get_positions --action all --address 0x1234...

# 查询账户余额
uv run python -m src.services.hyperliquid.cli_main get_balance --address 0x1234...
```

### Alchemy Service

```bash
# 查询多链资产组合
uv run python -m src.services.alchemy.cli portfolio --address 0x... --networks eth,base,arb,op

# 查询原生代币余额
uv run python -m src.services.alchemy.cli native-balance --address 0x... --network eth
```

> 注意：Alchemy API 仅支持 EVM 链，不支持 Solana 资产查询。

### Privy Service

```bash
# 获取用户资料（含钱包地址）
uv run python -m src.services.privy.cli profile --jwt <token>
```

---

## card 模块

card 模块不通过命令行运行，作为 Python 模块被 Agent 调用。

```python
from src.tools.card import (
    build_open_long_params,
    build_open_short_params,
    action_open_position,
    build_close_position_params,
    action_close_position,
    build_set_tpsl_params,
    action_set_tpsl,
    build_update_leverage_params,
    action_update_leverage,
    build_view_position_params,
    action_view_position,
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

---

## 环境变量

| 变量 | 说明 |
|------|------|
| `COINGECKO_PRO_API_KEY` | CoinGecko Pro API 密钥（有付费密钥时自动使用 pro 接口） |
| `ALCHEMY_API_KEY` | Alchemy API 密钥（用于查询链上资产） |
| `MYDEX_API_BASE` | Mydex 后端 API 地址（默认 https://test.mydex.io） |
| `JWT` | Privy JWT token（用于 CLI 调试 Privy 服务） |
