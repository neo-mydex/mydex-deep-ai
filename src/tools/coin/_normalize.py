"""
代币符号/ID 标准化

维护常用代币符号到 CoinGecko ID 的映射表
"""

from typing import Any


# 常用代币符号 -> CoinGecko ID 映射
SYMBOL_TO_ID: dict[str, str] = {
    # 主流币
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    # L2/L1
    "arb": "arbitrum",
    "op": "optimism",
    "matic": "matic-network",
    "avax": "avalanche-2",
    "near": "near",
    "apt": "aptos",
    "sui": "sui",
    "sei": "sei-network",
    "inj": "injective-protocol",
    "atom": "cosmos",
    "dot": "polkadot",
    "ksm": "kusama",
    "ldo": "lido-dao",
    "mkr": "maker",
    "aave": "aave",
    "crv": "curve-dao-token",
    "snx": "havven",
    # DeFi
    "uni": "uniswap",
    "sushi": "sushi",
    "ape": "apecoin",
    "link": "chainlink",
    "mav": "mav",
    # 动物币
    "doge": "dogecoin",
    "shib": "shiba-inu",
    "pepe": "pepe",
    "wif": "dogwifcoin",
    # Memecoin
    "bonk": "bonk",
    "popcat": "popcat",
    # 稳定币
    "usdc": "usd-coin",
    "usdt": "tether",
    "dai": "dai",
}


def symbol_to_id(symbol: str) -> str:
    """
    将代币符号转换为 CoinGecko ID

    参数:
        symbol: 代币符号（不区分大小写）

    返回:
        CoinGecko ID
    """
    return SYMBOL_TO_ID.get(symbol.lower(), symbol.lower())


def is_contract_address(value: str) -> bool:
    """
    判断是否为合约地址

    参数:
        value: 待检查的字符串

    返回:
        是否为合约地址
    """
    # EVM 地址
    if value.startswith("0x") and len(value) == 42:
        return True
    # Solana 地址 (32-44 字符)
    if 32 <= len(value) <= 44 and value.isalnum():
        return True
    return False


def normalize_symbol(symbol: str) -> str:
    """
    标准化代币符号

    参数:
        symbol: 代币符号

    返回:
        标准化后的符号（大写）
    """
    return symbol.strip().lower()


# 网络名称 -> CoinGecko platform 名称映射
NETWORK_TO_COINGECKO: dict[str, str] = {
    "eth": "ethereum",
    "ethereum": "ethereum",
    "base": "base",
    "arb": "arbitrum-one",
    "arbitrum": "arbitrum-one",
    "arbitrum-one": "arbitrum-one",
    "op": "optimistic-ethereum",
    "optimism": "optimistic-ethereum",
    "polygon": "polygon-pos",
    "matic": "polygon-pos",
    "bnb": "binance-smart-chain",
    "bsc": "binance-smart-chain",
    "avax": "avalanche-2",
    "avalanche": "avalanche-2",
    "sol": "solana",
    "solana": "solana",
}
