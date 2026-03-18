import json
import os
import re
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)

COINGECKO_PRO_API_KEY = os.getenv("COINGECKO_PRO_API_KEY")
COINGECKO_API_BASE = (
    "https://pro-api.coingecko.com/api/v3"
    if COINGECKO_PRO_API_KEY
    else "https://api.coingecko.com/api/v3"
)
COINGECKO_ONCHAIN_API_BASE = COINGECKO_API_BASE
DEFAULT_TIMEOUT_SECONDS = 15

NETWORK_PLATFORM_MAP = {
    "eth": "ethereum",
    "ethereum": "ethereum",
    "base": "base",
    "arbitrum": "arbitrum-one",
    "arb": "arbitrum-one",
    "sol": "solana",
    "solana": "solana",
    "bsc": "binance-smart-chain",
    "bnb": "binance-smart-chain",
    "polygon": "polygon-pos",
    "matic": "polygon-pos",
    "avax": "avalanche",
    "avalanche": "avalanche",
}

NETWORK_ONCHAIN_MAP = {
    "eth": "eth",
    "ethereum": "eth",
    "base": "base",
    "arbitrum": "arbitrum",
    "arbitrum-one": "arbitrum",
    "arb": "arbitrum",
    "sol": "solana",
    "solana": "solana",
    "bsc": "bsc",
    "bnb": "bsc",
    "binance-smart-chain": "bsc",
    "polygon": "polygon_pos",
    "polygon-pos": "polygon_pos",
    "matic": "polygon_pos",
    "avax": "avax",
    "avalanche": "avax",
}

ADDRESS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^0x[a-fA-F0-9]{40}$"), "ethereum"),
    (re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$"), "solana"),
    (re.compile(r"^0x[a-fA-F0-9]{64}$"), "sui"),
    (re.compile(r"^[EQHU][Q_A-Za-z0-9+-]{47}$"), "ton"),
    (re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$"), "tron"),
]

EVM_FALLBACK_NETWORKS = [
    "ethereum",
    "binance-smart-chain",
    "base",
    "arbitrum-one",
    "optimistic-ethereum",
]


class QueryInput(BaseModel):
    query: str
    network: str | None = None


class CandidateToken(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    coin_gecko_id: str = Field(alias="coinGeckoId")
    name: str
    symbol: str
    market_cap_rank: int | None = Field(default=None, alias="marketCapRank")


class SelectedCoin(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    coin_gecko_id: str = Field(alias="coinGeckoId")
    name: str
    symbol: str
    network: str | None = None
    address: str | None = None


class PriceDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    usd: float | None = None
    usd_market_cap: float | None = Field(default=None, alias="usdMarketCap")
    usd_24h_vol: float | None = Field(default=None, alias="usd24hVol")
    usd_24h_change: float | None = Field(default=None, alias="usd24hChange")
    last_updated_at: str | None = Field(default=None, alias="lastUpdatedAt")


class OutputMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    source: Literal["search", "contract_lookup", "error"]
    message: str | None = None


class TokenSearchResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    input: QueryInput
    mode: Literal["coin_info_service_cli"] = "coin_info_service_cli"
    selected_coin: SelectedCoin | None = Field(default=None, alias="selectedCoin")
    price_detail: PriceDetail | None = Field(default=None, alias="priceDetail")
    metadata: OutputMetadata
    primary_network: str | None = Field(default=None, alias="primaryNetwork")
    network_candidate_count: int = Field(default=0, alias="networkCandidateCount")
    candidates: list[CandidateToken] = Field(default_factory=list)
    final_source: str = Field(alias="finalSource")


def parse_args(argv: list[str]) -> QueryInput:
    parser = ArgumentParser(
        description="Search token price by symbol, name, or contract address."
    )
    parser.add_argument(
        "-c",
        "--coin",
        "--token",
        dest="query",
        required=True,
        help="Coin name, symbol, or token address.",
    )
    parser.add_argument(
        "-n",
        "--network",
        dest="network",
        help="Optional network filter, e.g. eth, base, arbitrum, sol, bsc.",
    )
    args = parser.parse_args(argv)
    return QueryInput(query=args.query.strip(), network=normalize_network(args.network))


def normalize_network(network: str | None) -> str | None:
    if not network:
        return None
    return NETWORK_PLATFORM_MAP.get(network.strip().lower(), network.strip().lower())


def normalize_onchain_network(network: str | None) -> str | None:
    if not network:
        return None
    return NETWORK_ONCHAIN_MAP.get(network.strip().lower(), network.strip().lower())


def fetch_json(url: str) -> dict[str, Any]:
    headers = {
        "accept": "application/json",
        "user-agent": "mydex-deep-cli-search-token/1.0",
    }
    if COINGECKO_PRO_API_KEY:
        headers["x-cg-pro-api-key"] = COINGECKO_PRO_API_KEY

    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"CoinGecko HTTP {exc.code}: {detail or exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"CoinGecko request failed: {exc.reason}") from exc


def is_contract_address(value: str) -> bool:
    if value.startswith("0x") and len(value) == 42:
        return True
    return 32 <= len(value) <= 44 and value.isalnum()


def infer_network_from_address(address: str) -> str | None:
    trimmed = address.strip()
    for pattern, network in ADDRESS_PATTERNS:
        if pattern.fullmatch(trimmed):
            return network
    return None


def is_evm_address(address: str) -> bool:
    return bool(re.fullmatch(r"^0x[a-fA-F0-9]{40}$", address.strip()))


def resolve_query_input(query: QueryInput) -> QueryInput:
    if query.network or not is_contract_address(query.query):
        return query

    inferred_network = infer_network_from_address(query.query)
    if not inferred_network:
        return query

    return QueryInput(query=query.query, network=inferred_network)


def contract_lookup(query: QueryInput) -> TokenSearchResponse:
    if not query.network:
        raise ValueError("Contract address lookup requires a network.")

    if is_evm_address(query.query) and query.network == "ethereum":
        return contract_lookup_with_fallbacks(query, EVM_FALLBACK_NETWORKS)

    return contract_lookup_single_network(query)


def contract_lookup_with_fallbacks(
    query: QueryInput, candidate_networks: list[str]
) -> TokenSearchResponse:
    last_error: Exception | None = None

    for network in candidate_networks:
        attempt = QueryInput(query=query.query, network=network)
        try:
            return contract_lookup_single_network(attempt)
        except RuntimeError as exc:
            last_error = exc
            if "HTTP 404" in str(exc):
                continue
            raise

    if last_error:
        raise last_error
    raise ValueError("No supported network matched this contract address.")


def contract_lookup_single_network(query: QueryInput) -> TokenSearchResponse:
    if not query.network:
        raise ValueError("Contract address lookup requires a network.")

    onchain_network = normalize_onchain_network(query.network)
    if onchain_network:
        try:
            return onchain_contract_lookup(query, onchain_network)
        except RuntimeError as exc:
            if "HTTP 404" not in str(exc):
                raise

    url = (
        f"{COINGECKO_API_BASE}/coins/{quote(query.network)}/contract/{quote(query.query)}"
        "?localization=false&tickers=false&market_data=true&community_data=false"
        "&developer_data=false&sparkline=false"
    )
    payload = fetch_json(url)
    return build_response(
        query=query,
        payload=payload,
        source="contract_lookup",
        candidates=[],
        primary_network=query.network,
        address=query.query,
    )


def onchain_contract_lookup(query: QueryInput, onchain_network: str) -> TokenSearchResponse:
    token_payload = fetch_json(
        f"{COINGECKO_ONCHAIN_API_BASE}/onchain/networks/{quote(onchain_network)}/tokens/{quote(query.query)}"
    )
    info_payload = fetch_json(
        f"{COINGECKO_ONCHAIN_API_BASE}/onchain/networks/{quote(onchain_network)}/tokens/{quote(query.query)}/info"
    )
    return build_onchain_response(
        query=query,
        token_payload=token_payload,
        info_payload=info_payload,
        primary_network=query.network,
        address=query.query,
    )


def search_lookup(query: QueryInput) -> TokenSearchResponse:
    search_payload = fetch_json(
        f"{COINGECKO_API_BASE}/search?query={quote(query.query)}"
    )
    coins = search_payload.get("coins", [])
    if not coins:
        raise ValueError(f"No token found for query: {query.query}")

    ranked_coins = rank_candidates_with_details(coins, query)
    candidates = [build_candidate(item) for item in ranked_coins[:5]]
    selected = ranked_coins[0]
    payload = fetch_coin_detail(selected["id"])
    primary_network = pick_primary_network(payload, query.network)
    return build_response(
        query=query,
        payload=payload,
        source="search",
        candidates=candidates,
        primary_network=primary_network,
        address=pick_address(payload, primary_network),
    )


def select_best_candidate(coins: list[dict[str, Any]], query: QueryInput) -> dict[str, Any]:
    return rank_candidates(coins, query)[0]


def rank_candidates(coins: list[dict[str, Any]], query: QueryInput) -> list[dict[str, Any]]:
    normalized_query = query.query.strip().lower()
    exact_matches: list[dict[str, Any]] = []
    partial_matches: list[dict[str, Any]] = []

    for item in coins:
        symbol = str(item.get("symbol", "")).lower()
        name = str(item.get("name", "")).lower()
        if normalized_query in {symbol, name}:
            exact_matches.append(item)
        else:
            partial_matches.append(item)

    candidate_pool = exact_matches or partial_matches or coins
    return sorted(candidate_pool, key=candidate_sort_key)


def rank_candidates_with_details(
    coins: list[dict[str, Any]], query: QueryInput
) -> list[dict[str, Any]]:
    ranked = rank_candidates(coins, query)
    enriched: list[dict[str, Any]] = []

    for item in ranked[:5]:
        enriched.append(enrich_candidate_market_cap_rank(item))

    enriched_ids = {item["id"] for item in enriched if item.get("id")}
    for item in ranked[5:]:
        if item.get("id") not in enriched_ids:
            enriched.append(item)

    return sorted(enriched, key=candidate_sort_key)


def enrich_candidate_market_cap_rank(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("market_cap_rank") is not None and item.get("market_cap_usd") is not None:
        return item

    coin_id = item.get("id")
    if not coin_id:
        return item

    try:
        detail = fetch_coin_detail(str(coin_id))
    except Exception:
        return item

    enriched = dict(item)
    enriched["market_cap_rank"] = detail.get("market_cap_rank")
    enriched["market_cap_usd"] = ((detail.get("market_data") or {}).get("market_cap") or {}).get("usd")
    return enriched


def candidate_sort_key(item: dict[str, Any]) -> tuple[int, float]:
    rank = item.get("market_cap_rank")
    market_cap_usd = item.get("market_cap_usd")
    rank_value = rank if isinstance(rank, int) else 10**9
    market_cap_value = float(market_cap_usd) if isinstance(market_cap_usd, (int, float)) else -1.0
    return (rank_value, -market_cap_value)


def fetch_coin_detail(coin_id: str) -> dict[str, Any]:
    return fetch_json(
        f"{COINGECKO_API_BASE}/coins/{quote(coin_id)}"
        "?localization=false&tickers=false&market_data=true&community_data=false"
        "&developer_data=false&sparkline=false"
    )


def pick_primary_network(payload: dict[str, Any], requested_network: str | None) -> str | None:
    platforms = payload.get("platforms") or {}
    if requested_network and platforms.get(requested_network):
        return requested_network
    for network, address in platforms.items():
        if address:
            return network
    return requested_network


def pick_address(payload: dict[str, Any], primary_network: str | None) -> str | None:
    platforms = payload.get("platforms") or {}
    if primary_network:
        return platforms.get(primary_network)
    for address in platforms.values():
        if address:
            return address
    return None


def build_candidate(item: dict[str, Any]) -> CandidateToken:
    return CandidateToken(
        coinGeckoId=item["id"],
        name=item["name"],
        symbol=str(item["symbol"]).upper(),
        marketCapRank=item.get("market_cap_rank"),
    )


def build_response(
    query: QueryInput,
    payload: dict[str, Any],
    source: Literal["search", "contract_lookup"],
    candidates: list[CandidateToken],
    primary_network: str | None,
    address: str | None,
) -> TokenSearchResponse:
    market_data = payload.get("market_data") or {}
    current_price = market_data.get("current_price") or {}
    return TokenSearchResponse(
        input=query,
        selectedCoin=SelectedCoin(
            coinGeckoId=payload["id"],
            name=payload["name"],
            symbol=str(payload["symbol"]).upper(),
            network=primary_network,
            address=address,
        ),
        priceDetail=PriceDetail(
            usd=current_price.get("usd"),
            usdMarketCap=market_data.get("market_cap", {}).get("usd"),
            usd24hVol=market_data.get("total_volume", {}).get("usd"),
            usd24hChange=market_data.get("price_change_percentage_24h"),
            lastUpdatedAt=payload.get("last_updated"),
        ),
        metadata=OutputMetadata(success=True, source=source),
        primaryNetwork=primary_network,
        networkCandidateCount=1 if primary_network else 0,
        candidates=candidates,
        finalSource=source,
    )


def build_onchain_response(
    query: QueryInput,
    token_payload: dict[str, Any],
    info_payload: dict[str, Any],
    primary_network: str | None,
    address: str,
) -> TokenSearchResponse:
    token_data = token_payload.get("data") or {}
    info_data = info_payload.get("data") or {}
    token_attributes = token_data.get("attributes") or {}
    info_attributes = info_data.get("attributes") or {}
    coingecko_coin_id = token_attributes.get("coingecko_coin_id")
    market_cap = token_attributes.get("market_cap_usd")
    volume_24h = (token_attributes.get("volume_usd") or {}).get("h24")
    price_usd = token_attributes.get("price_usd")
    last_trade_timestamp = token_attributes.get("last_trade_timestamp")

    return TokenSearchResponse(
        input=query,
        selectedCoin=SelectedCoin(
            coinGeckoId=coingecko_coin_id or token_data.get("id") or address,
            name=info_attributes.get("name") or token_attributes.get("name") or address,
            symbol=str(info_attributes.get("symbol") or token_attributes.get("symbol") or "").upper(),
            network=primary_network,
            address=address,
        ),
        priceDetail=PriceDetail(
            usd=safe_float(price_usd),
            usdMarketCap=safe_float(market_cap),
            usd24hVol=safe_float(volume_24h),
            usd24hChange=None,
            lastUpdatedAt=str(last_trade_timestamp) if last_trade_timestamp is not None else None,
        ),
        metadata=OutputMetadata(success=True, source="contract_lookup"),
        primaryNetwork=primary_network,
        networkCandidateCount=1 if primary_network else 0,
        candidates=[],
        finalSource="contract_lookup_onchain",
    )


def build_error_response(query: QueryInput, message: str) -> TokenSearchResponse:
    return TokenSearchResponse(
        input=query,
        metadata=OutputMetadata(success=False, source="error", message=message),
        candidates=[],
        finalSource="error",
    )


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> int:
    query = resolve_query_input(parse_args(sys.argv[1:]))
    try:
        result = contract_lookup(query) if is_contract_address(query.query) else search_lookup(query)
        print(result.model_dump_json(by_alias=True, indent=2))
        return 0
    except Exception as exc:
        print(build_error_response(query, str(exc)).model_dump_json(by_alias=True, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
