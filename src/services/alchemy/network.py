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
    "avax": "avax-mainnet",
    "avalanche": "avax-mainnet",
}


NATIVE_TOKEN_METADATA = {
    "eth-mainnet": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
    "base-mainnet": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
    "arb-mainnet": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
    "opt-mainnet": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
    "polygon-mainnet": {"symbol": "POL", "name": "Polygon", "decimals": 18},
    "bnb-mainnet": {"symbol": "BNB", "name": "BNB", "decimals": 18},
    "avax-mainnet": {"symbol": "AVAX", "name": "Avalanche", "decimals": 18},
    "sol-mainnet": {"symbol": "SOL", "name": "Solana", "decimals": 9},
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
