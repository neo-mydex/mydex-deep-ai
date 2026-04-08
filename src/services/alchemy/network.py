"""
网络配置和标准化
"""


NETWORK_MAP = {
    "eth": "eth-mainnet",
    "ethereum": "eth-mainnet",
    "mainnet": "eth-mainnet",
    "base": "base-mainnet",
    "arb": "arb-mainnet",
    "arbitrum": "arb-mainnet",
    "arbitrum-one": "arb-mainnet",
    "op": "opt-mainnet",
    "optimism": "opt-mainnet",
    "optimistic-ethereum": "opt-mainnet",
    "polygon": "polygon-mainnet",
    "matic": "polygon-mainnet",
    "bnb": "bnb-mainnet",
    "bsc": "bnb-mainnet",
    "binance-smart-chain": "bnb-mainnet",
    "sol": "sol-mainnet",
    "solana": "sol-mainnet",
    "monad": "monad-mainnet",
    "ink": "ink-mainnet",
    "hyperliquid": "hyperliquid-mainnet",
}


NATIVE_TOKEN_METADATA = {
    # 1  Ethereum
    "eth-mainnet": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
    # 2  Base
    "base-mainnet": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
    # 3  Arbitrum
    "arb-mainnet": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
    # 4  Optimism
    "opt-mainnet": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
    # 5  Polygon
    "polygon-mainnet": {"symbol": "POL", "name": "Polygon", "decimals": 18},
    # 6  BSC
    "bnb-mainnet": {"symbol": "BNB", "name": "BNB", "decimals": 18},
    # 7  Solana
    "sol-mainnet": {"symbol": "SOL", "name": "Solana", "decimals": 9},
    # 8  Monad
    "monad-mainnet": {"symbol": "MON", "name": "Monad", "decimals": 18},
    # 9  Ink
    "ink-mainnet": {"symbol": "INK", "name": "Ink", "decimals": 18},
    # 10 Hyperliquid
    "hyperliquid-mainnet": {"symbol": "HYPE", "name": "Hyperliquid", "decimals": 18},
}


def normalize_network(network: str) -> str:
    """
    标准化网络名称

    参数:
        network: 原始网络名称

    返回:
        标准化后的网络名称
    """
    normalized = network.strip().lower()
    return NETWORK_MAP.get(normalized, normalized)
