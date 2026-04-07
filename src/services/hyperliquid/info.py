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


def get_all_mids(
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, str]:
    """获取所有币种的中间价"""
    info = _build_info(network, timeout=timeout)
    result = info.all_mids(dex=dex)
    return result if isinstance(result, dict) else {}


def get_meta(
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict:
    """获取交易所永续合约元数据"""
    info = _build_info(network, timeout=timeout)
    return info.meta(dex=dex)


def get_meta_and_asset_ctxs(
    network: Network = "mainnet",
    timeout: float | None = None,
) -> list:
    """获取交易所元数据+资产上下文（含 maxLeverage, onlyIsolated 等）"""
    info = _build_info(network, timeout=timeout)
    return info.meta_and_asset_ctxs()


def user_state(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict:
    """获取用户状态"""
    info = _build_info(network, timeout=timeout)
    return info.user_state(address=address, dex=dex)


def open_orders(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> list[dict]:
    """获取用户所有挂单（原始数据）"""
    info = _build_info(network, timeout=timeout)
    return info.open_orders(address=address, dex=dex)


def frontend_open_orders(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> list[dict]:
    """获取用户挂单（含 TP/SL 等前端信息）"""
    info = _build_info(network, timeout=timeout)
    result = info.frontend_open_orders(address=address, dex=dex)
    return result if isinstance(result, list) else []
