import json
import os
import sys
from argparse import ArgumentParser
from decimal import Decimal, InvalidOperation, getcontext
from pathlib import Path
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


getcontext().prec = 50

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY") or "docs-demo"
ALCHEMY_DATA_API_BASE = f"https://api.g.alchemy.com/data/v1/{ALCHEMY_API_KEY}"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_PAGE_SIZE = 100

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


class WalletInput(BaseModel):
    wallet: str
    networks: list[str]


class WalletAsset(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    network: str
    wallet: str
    token_address: str | None = Field(default=None, alias="tokenAddress")
    symbol: str | None = None
    name: str | None = None
    decimals: int | None = None
    logo: str | None = None
    raw_balance: str | None = Field(default=None, alias="rawBalance")
    balance: str | None = None
    price_usd: str | None = Field(default=None, alias="priceUsd")
    value_usd: str | None = Field(default=None, alias="valueUsd")
    last_updated_at: str | None = Field(default=None, alias="lastUpdatedAt")
    is_native_token: bool = Field(default=False, alias="isNativeToken")


class NetworkBreakdown(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    network: str
    asset_count: int = Field(alias="assetCount")
    total_value_usd: str = Field(alias="totalValueUsd")


class PortfolioSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    asset_count: int = Field(alias="assetCount")
    network_count: int = Field(alias="networkCount")
    total_value_usd: str = Field(alias="totalValueUsd")


class OutputMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    source: Literal["alchemy_portfolio", "error"]
    message: str | None = None
    api_key_source: Literal["env", "docs-demo"] = Field(alias="apiKeySource")


class WalletPortfolioResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    input: WalletInput
    mode: Literal["wallet_portfolio_cli"] = "wallet_portfolio_cli"
    summary: PortfolioSummary | None = None
    breakdown: list[NetworkBreakdown] = Field(default_factory=list)
    assets: list[WalletAsset] = Field(default_factory=list)
    page_key: str | None = Field(default=None, alias="pageKey")
    metadata: OutputMetadata
    final_source: Literal["alchemy_tokens_by_address", "error"] = Field(alias="finalSource")


def parse_args(argv: list[str]) -> WalletInput:
    parser = ArgumentParser(description="Fetch wallet token portfolio by address and network.")
    parser.add_argument(
        "-w",
        "--wallet",
        dest="wallet",
        required=True,
        help="Wallet address or ENS/SNS-style address string supported by Alchemy.",
    )
    parser.add_argument(
        "-n",
        "--network",
        dest="network",
        required=True,
        help="One or more networks, comma-separated. Example: eth or eth,base,arb",
    )
    args = parser.parse_args(argv)
    networks = [normalize_network(part) for part in args.network.split(",") if part.strip()]
    deduped_networks = list(dict.fromkeys(networks))
    if not deduped_networks:
        raise ValueError("At least one network is required.")
    return WalletInput(wallet=args.wallet.strip(), networks=deduped_networks)


def normalize_network(network: str) -> str:
    normalized = network.strip().lower()
    return NETWORK_MAP.get(normalized, normalized)


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "mydex-deep-cli-wallet/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Alchemy HTTP {exc.code}: {detail or exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Alchemy request failed: {exc.reason}") from exc


def build_request_body(wallet_input: WalletInput, page_key: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "addresses": [
            {
                "address": wallet_input.wallet,
                "networks": wallet_input.networks,
            }
        ],
        "withMetadata": True,
        "withPrices": True,
        "includeNativeTokens": True,
        "includeErc20Tokens": True,
        "pageSize": DEFAULT_PAGE_SIZE,
    }
    if page_key:
        payload["pageKey"] = page_key
    return payload


def fetch_all_wallet_assets(wallet_input: WalletInput) -> tuple[list[dict[str, Any]], str | None]:
    page_key: str | None = None
    merged_assets: dict[tuple[str, str, str | None], dict[str, Any]] = {}
    final_page_key: str | None = None

    while True:
        body = build_request_body(wallet_input, page_key=page_key)
        tokens_payload = post_json(f"{ALCHEMY_DATA_API_BASE}/assets/tokens/by-address", body)
        balances_payload = post_json(
            f"{ALCHEMY_DATA_API_BASE}/assets/tokens/balances/by-address",
            {
                "addresses": body["addresses"],
                "includeNativeTokens": True,
                "includeErc20Tokens": True,
                "pageSize": DEFAULT_PAGE_SIZE,
                **({"pageKey": page_key} if page_key else {}),
            },
        )

        token_items = ((tokens_payload.get("data") or {}).get("tokens")) or []
        balance_items = ((balances_payload.get("data") or {}).get("tokens")) or []

        for item in token_items:
            key = asset_key(item)
            merged_assets[key] = dict(item)

        for item in balance_items:
            key = asset_key(item)
            merged_assets[key] = merge_asset_payload(merged_assets.get(key), item)

        final_page_key = (tokens_payload.get("data") or {}).get("pageKey") or (balances_payload.get("data") or {}).get("pageKey")
        if not final_page_key or final_page_key == page_key:
            break
        page_key = final_page_key

    return list(merged_assets.values()), final_page_key


def asset_key(item: dict[str, Any]) -> tuple[str, str, str | None]:
    return (
        str(item.get("network") or ""),
        str(item.get("address") or ""),
        item.get("tokenAddress"),
    )


def merge_asset_payload(existing: dict[str, Any] | None, incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing or {})
    for key, value in incoming.items():
        if value is not None or key not in merged:
            merged[key] = value
    return merged


def map_asset(item: dict[str, Any]) -> WalletAsset:
    metadata = dict(item.get("tokenMetadata") or {})
    if item.get("tokenAddress") is None:
        metadata = merge_native_metadata_defaults(
            metadata,
            NATIVE_TOKEN_METADATA.get(str(item.get("network") or ""), {}),
        )
    prices = item.get("tokenPrices") or []
    usd_price = next(
        (price for price in prices if str(price.get("currency", "")).lower() == "usd"),
        None,
    )
    raw_balance = item.get("tokenBalance")
    decimals = metadata.get("decimals")
    normalized_balance = normalize_token_balance(raw_balance, decimals)
    price_value = decimal_or_none(usd_price.get("value") if usd_price else None)
    value_usd = (
        normalized_balance * price_value
        if normalized_balance is not None and price_value is not None
        else None
    )

    return WalletAsset(
        network=str(item.get("network") or ""),
        wallet=str(item.get("address") or ""),
        tokenAddress=item.get("tokenAddress"),
        symbol=metadata.get("symbol"),
        name=metadata.get("name"),
        decimals=decimals if isinstance(decimals, int) else None,
        logo=metadata.get("logo"),
        rawBalance=format_raw_balance(raw_balance),
        balance=format_decimal(normalized_balance),
        priceUsd=format_decimal(price_value),
        valueUsd=format_decimal(value_usd),
        lastUpdatedAt=usd_price.get("lastUpdatedAt") if usd_price else None,
        isNativeToken=item.get("tokenAddress") is None,
    )


def merge_native_metadata_defaults(
    metadata: dict[str, Any], defaults: dict[str, Any]
) -> dict[str, Any]:
    merged = dict(metadata)
    for key, value in defaults.items():
        if merged.get(key) in (None, ""):
            merged[key] = value
    return merged


def normalize_token_balance(raw_balance: Any, decimals: Any) -> Decimal | None:
    raw_decimal = decimal_or_none(raw_balance)
    if raw_decimal is None:
        return None
    if not isinstance(decimals, int):
        return raw_decimal
    return raw_decimal / (Decimal(10) ** decimals)


def decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, str) and value.lower().startswith("0x"):
        try:
            return Decimal(int(value, 16))
        except ValueError:
            return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def format_raw_balance(value: Any) -> str | None:
    decimal_value = decimal_or_none(value)
    return format_decimal(decimal_value)


def format_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    normalized = value.normalize()
    return format(normalized, "f") if normalized == normalized.to_integral() else format(normalized, "f").rstrip("0").rstrip(".")


def build_response(wallet_input: WalletInput, items: list[dict[str, Any]], page_key: str | None) -> WalletPortfolioResponse:
    assets = [map_asset(item) for item in items]
    assets = [
        asset
        for asset in assets
        if (decimal_or_none(asset.balance) or Decimal("0")) > 0
    ]
    assets.sort(key=lambda asset: decimal_or_none(asset.value_usd) or Decimal("-1"), reverse=True)

    totals_by_network: dict[str, Decimal] = {}
    counts_by_network: dict[str, int] = {}
    total_value = Decimal("0")

    for asset in assets:
        asset_value = decimal_or_none(asset.value_usd) or Decimal("0")
        totals_by_network[asset.network] = totals_by_network.get(asset.network, Decimal("0")) + asset_value
        counts_by_network[asset.network] = counts_by_network.get(asset.network, 0) + 1
        total_value += asset_value

    breakdown = [
        NetworkBreakdown(
            network=network,
            assetCount=counts_by_network[network],
            totalValueUsd=format_decimal(totals_by_network[network]) or "0",
        )
        for network in sorted(totals_by_network, key=lambda key: totals_by_network[key], reverse=True)
    ]

    return WalletPortfolioResponse(
        input=wallet_input,
        summary=PortfolioSummary(
            assetCount=len(assets),
            networkCount=len(wallet_input.networks),
            totalValueUsd=format_decimal(total_value) or "0",
        ),
        breakdown=breakdown,
        assets=assets,
        pageKey=page_key,
        metadata=OutputMetadata(
            success=True,
            source="alchemy_portfolio",
            apiKeySource="env" if ALCHEMY_API_KEY != "docs-demo" else "docs-demo",
        ),
        finalSource="alchemy_tokens_by_address",
    )


def build_error_response(wallet_input: WalletInput, message: str) -> WalletPortfolioResponse:
    return WalletPortfolioResponse(
        input=wallet_input,
        metadata=OutputMetadata(
            success=False,
            source="error",
            message=message,
            apiKeySource="env" if ALCHEMY_API_KEY != "docs-demo" else "docs-demo",
        ),
        finalSource="error",
    )


def main() -> int:
    wallet_input = parse_args(sys.argv[1:])
    try:
        items, page_key = fetch_all_wallet_assets(wallet_input)
        print(build_response(wallet_input, items, page_key).model_dump_json(by_alias=True, indent=2))
        return 0
    except Exception as exc:
        print(build_error_response(wallet_input, str(exc)).model_dump_json(by_alias=True, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
