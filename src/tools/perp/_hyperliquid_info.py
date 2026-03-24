"""
Hyperliquid 基础信息模块

提供通用的 network 配置和 Info 实例构建函数
"""

from typing import Literal

from hyperliquid.info import Info
from hyperliquid.utils import constants

Network = Literal["mainnet", "testnet"]


def _get_base_url(network: Network) -> str:
    """获取 API Base URL"""
    if network == "mainnet":
        return constants.MAINNET_API_URL
    if network == "testnet":
        return constants.TESTNET_API_URL
    raise ValueError(f"Unsupported network: {network}")


def _build_info(network: Network = "mainnet", timeout: float | None = None) -> Info:
    """构建 Info 实例（只读模式）"""
    if network == "testnet":
        return Info(
            _get_base_url(network),
            skip_ws=True,
            timeout=timeout,
            spot_meta={"universe": [], "tokens": []},
        )
    return Info(_get_base_url(network), skip_ws=True, timeout=timeout)
