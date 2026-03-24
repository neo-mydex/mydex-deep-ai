"""
Hyperliquid Card 类型定义

Card 类型:
- OPEN_LONG: 开多
- OPEN_SHORT: 开空
- CLOSE_POSITION: 平仓
- SET_TPSL: 设置止盈止损
- VIEW_POSITION: 查看仓位
- UPDATE_LEVERAGE: 更新杠杆
"""

from typing import Literal

# Card 类型
CardType = Literal["OPEN_LONG", "OPEN_SHORT", "CLOSE_POSITION", "SET_TPSL", "VIEW_POSITION", "UPDATE_LEVERAGE"]

# 保证金模式
MarginMode = Literal["cross", "isolated"]

# 订单类型
OrderType = Literal["market", "limit"]

# 持仓方向
PositionSide = Literal["long", "short", "flat"]

# 交易方向（Hyperliquid API 格式）
TradeSide = Literal["buy", "sell"]

# 网络
Network = Literal["mainnet", "testnet"]
