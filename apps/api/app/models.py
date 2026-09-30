"""MarketReality OS – Normalized data models.

Every model includes provenance metadata so findings can be traced
back to their CMC source endpoint and timestamp.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────

class RealityState(str, Enum):
    REPRESENTATIVE = "REPRESENTATIVE"
    PARTIALLY_REPRESENTATIVE = "PARTIALLY_REPRESENTATIVE"
    FRAGMENTED = "FRAGMENTED"
    CONCENTRATED = "CONCENTRATED"
    INCONSISTENT = "INCONSISTENT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class TradabilityState(str, Enum):
    STRUCTURALLY_SUPPORTED = "STRUCTURALLY_SUPPORTED"
    CONDITIONAL = "CONDITIONAL"
    CONSTRAINED = "CONSTRAINED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class EvidenceQuality(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    LIMITED = "LIMITED"
    INSUFFICIENT = "INSUFFICIENT"


class FreshnessState(str, Enum):
    FRESH = "FRESH"
    AGING = "AGING"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class MarketType(str, Enum):
    CEX = "CEX"
    DEX = "DEX"
    UNKNOWN = "UNKNOWN"


# ── Evidence ───────────────────────────────────────────────────────

class Evidence(BaseModel):
    evidence_id: str
    finding: str
    value: Any
    unit: str | None = None
    source_endpoint: str
    source_timestamp: str | None = None
    observation_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    calculation: str
    inputs: list[str] = Field(default_factory=list)
    sample_size: int | None = None
    limitation: str | None = None


# ── Asset identity ────────────────────────────────────────────────

class Asset(BaseModel):
    symbol: str
    name: str | None = None
    slug: str | None = None
    cmc_id: int | None = None
    cmc_rank: int | None = None
    is_active: bool = True


# ── Market pair ───────────────────────────────────────────────────

class MarketPair(BaseModel):
    exchange_name: str
    exchange_slug: str | None = None
    exchange_id: int | None = None
    market_pair: str
    market_type: MarketType = MarketType.UNKNOWN
    category: str | None = None  # "spot", "derivatives", etc.
    base_symbol: str | None = None
    quote_symbol: str | None = None
    price_usd: float | None = None
    volume_24h_usd: float | None = None
    volume_percent: float | None = None
    effective_liquidity: float | None = None
    last_updated: str | None = None


class Venue(BaseModel):
    name: str
    slug: str | None = None
    exchange_id: int | None = None
    market_type: MarketType = MarketType.UNKNOWN
    total_volume_24h_usd: float = 0.0
    pair_count: int = 0
    volume_share: float = 0.0  # fraction of total observed


# ── Price observations ────────────────────────────────────────────

class PriceObservation(BaseModel):
    source: str  # exchange name or "CMC headline"
    price_usd: float
    timestamp: str | None = None


class VolumeObservation(BaseModel):
    source: str
    volume_24h_usd: float
    timestamp: str | None = None


# ── Global context ────────────────────────────────────────────────

class GlobalMarketContext(BaseModel):
    total_market_cap_usd: float | None = None
    total_volume_24h_usd: float | None = None
    btc_dominance: float | None = None
    eth_dominance: float | None = None
    active_cryptocurrencies: int | None = None
    active_exchanges: int | None = None
    total_market_pairs: int | None = None
    last_updated: str | None = None
    source_endpoint: str = "/v1/global-metrics/quotes/latest"


# ── Reality dimensions ────────────────────────────────────────────

class RealityDimension(BaseModel):
    name: str
    state: str
    value: float | None = None
    display_value: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    description: str | None = None


# ── Reality Gap ───────────────────────────────────────────────────

class RealityGap(BaseModel):
    headline_volume_24h: float | None = None
    headline_market_cap: float | None = None
    headline_price: float | None = None
    observed_pair_count: int = 0
    observed_total_volume: float | None = None
    top5_concentration: float | None = None
    top1_venue_share: float | None = None
    price_dispersion_pct: float | None = None
    coverage_state: str = "INSUFFICIENT_EVIDENCE"
    # Enriched fields from CMC quotes endpoint (free tier)
    cex_volume_24h: float | None = None
    dex_volume_24h: float | None = None
    pct_change_1h: float | None = None
    pct_change_24h: float | None = None
    pct_change_7d: float | None = None
    market_cap_dominance: float | None = None
    num_market_pairs_cmc: int | None = None   # CMC's own reported pair count
    circulating_supply: float | None = None


# ── Trade Reality ─────────────────────────────────────────────────

class TradeRealityRequest(BaseModel):
    symbol: str
    trade_size_usd: float
    side: str = "BUY"  # BUY or SELL


class TradeRealityDimension(BaseModel):
    name: str
    state: str
    value: float | None = None
    display_value: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class TradeRealityResult(BaseModel):
    asset: str
    trade_size_usd: float
    side: str
    result: TradabilityState
    dimensions: list[TradeRealityDimension]
    evidence: list[Evidence]
    limitations: list[str]
    observation_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Stress scenarios ──────────────────────────────────────────────

class StressScenario(BaseModel):
    id: str
    name: str
    description: str
    parameter: str | None = None
    value: float | None = None


class StressResult(BaseModel):
    scenario: StressScenario
    before: dict[str, Any]
    after: dict[str, Any]
    affected_dimensions: list[str]
    evidence: list[Evidence]
    observation_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Market Passport ───────────────────────────────────────────────

class MarketPassport(BaseModel):
    asset: Asset
    observation_timestamp: str
    market_state: dict[str, Any]
    structure: dict[str, Any]
    trade_reality: dict[str, Any] | None = None
    evidence_summary: list[Evidence]
    cmc_endpoints_used: list[str]
    limitations: list[str]


# ── Full Reality Report ──────────────────────────────────────────

class DataMode(str, Enum):
    LIVE   = "LIVE"
    CACHED = "CACHED"
    UNAVAILABLE = "UNAVAILABLE"


class RealityReport(BaseModel):
    asset: str
    asset_info: Asset | None = None
    status: str
    observation_timestamp: str
    dimensions: list[RealityDimension]
    reality_gap: RealityGap | None = None
    venues: list[Venue] = Field(default_factory=list)
    market_pairs_sample: list[MarketPair] = Field(default_factory=list)
    evidence: list[Evidence]
    global_context: GlobalMarketContext | None = None
    limitations: list[str]
    cmc_endpoints_used: list[str] = Field(default_factory=list)
    # Data transparency fields — always present, never omitted
    is_demo: bool = False
    data_mode: DataMode = DataMode.LIVE
    data_observation: str = "LIVE CMC DATA"
