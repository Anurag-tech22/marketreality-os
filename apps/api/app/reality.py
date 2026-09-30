"""MarketReality OS – Deterministic Reality Engine.

This module is the calculation core. It takes normalized CMC data and
produces deterministic evidence objects and reality dimensions.

AI is NOT used here. Every finding is reproducible from the inputs.
"""

from __future__ import annotations

import statistics
from datetime import datetime, timezone
from typing import Any

from .models import (
    Asset,
    Evidence,
    EvidenceQuality,
    FreshnessState,
    GlobalMarketContext,
    MarketPair,
    MarketType,
    RealityDimension,
    RealityGap,
    RealityReport,
    RealityState,
    StressResult,
    StressScenario,
    TradeRealityDimension,
    TradeRealityResult,
    TradabilityState,
    Venue,
)


# ── Helpers ────────────────────────────────────────────────────────

def _safe_float(value: Any) -> float | None:
    """Safely convert a value to float, returning None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.1%}"


def _usd(value: float | None) -> str:
    if value is None:
        return "N/A"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.2f}"


# ── Evidence counter ──────────────────────────────────────────────

class EvidenceCounter:
    """Generates sequential evidence IDs within a single report."""
    def __init__(self):
        self._count = 0

    def next_id(self) -> str:
        self._count += 1
        return f"EV-{self._count:03d}"


# ── Market pair normalization ─────────────────────────────────────

def normalize_market_pairs(raw_pairs: list[dict]) -> list[MarketPair]:
    """Normalize raw CMC market pair data into MarketPair objects."""
    pairs: list[MarketPair] = []
    for item in raw_pairs:
        if not isinstance(item, dict):
            continue

        exchange = item.get("exchange", {}) or {}
        quote = item.get("quote", {}) or {}
        usd = quote.get("USD", {}) or {}

        # Determine market type
        category = item.get("category", "")
        market_type = MarketType.UNKNOWN
        if isinstance(category, str):
            cat_lower = category.lower()
            if "spot" in cat_lower:
                market_type = MarketType.CEX
            elif "dex" in cat_lower or "defi" in cat_lower:
                market_type = MarketType.DEX

        pair_name = item.get("market_pair", "")
        base_asset = item.get("market_pair_base", {}) or {}
        quote_asset = item.get("market_pair_quote", {}) or {}

        pairs.append(MarketPair(
            exchange_name=exchange.get("name", "Unknown"),
            exchange_slug=exchange.get("slug"),
            exchange_id=exchange.get("id"),
            market_pair=pair_name,
            market_type=market_type,
            category=category,
            base_symbol=base_asset.get("currency_symbol") or base_asset.get("exchange_symbol"),
            quote_symbol=quote_asset.get("currency_symbol") or quote_asset.get("exchange_symbol"),
            price_usd=_safe_float(usd.get("price")),
            volume_24h_usd=_safe_float(usd.get("volume_24h")),
            volume_percent=_safe_float(usd.get("volume_percentage")),
            effective_liquidity=_safe_float(usd.get("effective_liquidity")),
            last_updated=usd.get("last_updated"),
        ))
    return pairs


# ── Venue aggregation ─────────────────────────────────────────────

def aggregate_venues(pairs: list[MarketPair]) -> list[Venue]:
    """Aggregate market pairs into venue-level statistics."""
    venue_map: dict[str, dict] = {}
    for p in pairs:
        name = p.exchange_name
        if name not in venue_map:
            venue_map[name] = {
                "name": name,
                "slug": p.exchange_slug,
                "exchange_id": p.exchange_id,
                "market_type": p.market_type,
                "volume": 0.0,
                "pair_count": 0,
            }
        if p.volume_24h_usd and p.volume_24h_usd > 0:
            venue_map[name]["volume"] += p.volume_24h_usd
        venue_map[name]["pair_count"] += 1

    total_volume = sum(v["volume"] for v in venue_map.values())

    venues = []
    for v in venue_map.values():
        venues.append(Venue(
            name=v["name"],
            slug=v["slug"],
            exchange_id=v["exchange_id"],
            market_type=v["market_type"],
            total_volume_24h_usd=v["volume"],
            pair_count=v["pair_count"],
            volume_share=v["volume"] / total_volume if total_volume > 0 else 0.0,
        ))

    # Sort by volume descending
    venues.sort(key=lambda x: x.total_volume_24h_usd, reverse=True)
    return venues


# ── Deterministic calculations ────────────────────────────────────

def calc_volume_concentration(
    pair_volumes: list[float], top_n: int = 5
) -> float | None:
    """Calculate top-N volume concentration ratio."""
    if not pair_volumes:
        return None
    total = sum(pair_volumes)
    if total <= 0:
        return None
    top = sum(sorted(pair_volumes, reverse=True)[:top_n])
    return top / total


def calc_venue_concentration(venues: list[Venue]) -> dict[str, float | None]:
    """Calculate venue-level concentration metrics."""
    if not venues:
        return {"top1": None, "top5": None}

    volumes = [v.total_volume_24h_usd for v in venues]
    total = sum(volumes)
    if total <= 0:
        return {"top1": None, "top5": None}

    sorted_vols = sorted(volumes, reverse=True)
    top1 = sorted_vols[0] / total
    top5 = sum(sorted_vols[:5]) / total

    return {"top1": top1, "top5": top5}


def calc_price_agreement(prices: list[float]) -> dict[str, Any]:
    """Calculate price agreement metrics across observed markets.

    Returns median, min, max, spread, dispersion, and agreement state.
    """
    if len(prices) < 2:
        return {
            "median": prices[0] if prices else None,
            "min": prices[0] if prices else None,
            "max": prices[0] if prices else None,
            "spread": 0.0,
            "dispersion_pct": 0.0,
            "outlier_count": 0,
            "state": "INSUFFICIENT_EVIDENCE" if not prices else "SINGLE_SOURCE",
            "sample_size": len(prices),
        }

    median_price = statistics.median(prices)
    min_price = min(prices)
    max_price = max(prices)
    spread = max_price - min_price

    if median_price > 0:
        dispersion_pct = (spread / median_price) * 100
    else:
        dispersion_pct = 0.0

    # Count outliers: prices more than 2% away from the median
    outlier_threshold = median_price * 0.02
    outliers = [p for p in prices if abs(p - median_price) > outlier_threshold]

    if dispersion_pct < 0.5:
        state = "HIGH_AGREEMENT"
    elif dispersion_pct < 2.0:
        state = "MODERATE_AGREEMENT"
    elif dispersion_pct < 5.0:
        state = "LOW_AGREEMENT"
    else:
        state = "INCONSISTENT"

    return {
        "median": median_price,
        "min": min_price,
        "max": max_price,
        "spread": spread,
        "dispersion_pct": dispersion_pct,
        "outlier_count": len(outliers),
        "state": state,
        "sample_size": len(prices),
    }


def calc_freshness(timestamps: list[str | None]) -> dict[str, Any]:
    """Evaluate data freshness from observed timestamps."""
    now = datetime.now(timezone.utc)
    valid_times: list[datetime] = []
    for ts in timestamps:
        if not ts:
            continue
        try:
            if ts.endswith("Z"):
                ts = ts[:-1] + "+00:00"
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            valid_times.append(dt)
        except (ValueError, TypeError):
            continue

    if not valid_times:
        return {
            "state": FreshnessState.UNKNOWN.value,
            "oldest_seconds": None,
            "newest_seconds": None,
            "median_age_seconds": None,
        }

    ages = [(now - t).total_seconds() for t in valid_times]
    oldest = max(ages)
    newest = min(ages)
    median_age = statistics.median(ages)

    # Freshness thresholds
    if median_age < 300:  # < 5 min
        state = FreshnessState.FRESH
    elif median_age < 3600:  # < 1 hour
        state = FreshnessState.AGING
    else:
        state = FreshnessState.STALE

    return {
        "state": state.value,
        "oldest_seconds": oldest,
        "newest_seconds": newest,
        "median_age_seconds": median_age,
    }


def calc_coverage_state(pair_count: int, venue_count: int) -> str:
    """Determine market coverage state from pair and venue counts."""
    if pair_count == 0:
        return RealityState.INSUFFICIENT_EVIDENCE.value
    if pair_count >= 100 and venue_count >= 20:
        return "HIGH"
    if pair_count >= 30 and venue_count >= 10:
        return "MODERATE"
    if pair_count >= 5:
        return "LOW"
    return "MINIMAL"


def detect_contradictions(
    headline_volume: float | None,
    observed_volume: float | None,
    concentration_top5: float | None,
    price_dispersion_pct: float | None,
    pair_count: int,
    venue_count: int,
    freshness_state: str,
) -> list[dict[str, str]]:
    """Detect structural contradictions in observed market data."""
    contradictions: list[dict[str, str]] = []

    # High volume but low coverage
    if headline_volume and headline_volume > 1_000_000_000 and pair_count < 20:
        contradictions.append({
            "type": "volume_coverage_mismatch",
            "description": (
                f"Headline volume is {_usd(headline_volume)} "
                f"but only {pair_count} market pairs observed."
            ),
            "severity": "HIGH",
        })

    # High concentration despite apparently broad activity
    if concentration_top5 and concentration_top5 > 0.80 and venue_count > 20:
        contradictions.append({
            "type": "concentration_despite_breadth",
            "description": (
                f"Top 5 pairs hold {_pct(concentration_top5)} of volume "
                f"despite {venue_count} venues observed."
            ),
            "severity": "MEDIUM",
        })

    # Large price divergence
    if price_dispersion_pct and price_dispersion_pct > 5.0:
        contradictions.append({
            "type": "price_divergence",
            "description": (
                f"Price dispersion of {price_dispersion_pct:.2f}% "
                "suggests fragmented or inconsistent market."
            ),
            "severity": "HIGH",
        })

    # Stale data
    if freshness_state == FreshnessState.STALE.value:
        contradictions.append({
            "type": "stale_data",
            "description": "Median data age exceeds 1 hour. Observations may not reflect current state.",
            "severity": "MEDIUM",
        })

    # Volume mismatch between headline and observed total
    if headline_volume and observed_volume and observed_volume > 0:
        ratio = observed_volume / headline_volume
        if ratio < 0.3:
            contradictions.append({
                "type": "observed_volume_undercount",
                "description": (
                    f"Observed pair volume ({_usd(observed_volume)}) is only "
                    f"{_pct(ratio)} of headline volume ({_usd(headline_volume)})."
                ),
                "severity": "MEDIUM",
            })

    return contradictions


def calc_evidence_quality(
    pair_count: int,
    venue_count: int,
    freshness_state: str,
    price_sample_size: int,
    has_contradictions: bool,
) -> EvidenceQuality:
    """Assess overall evidence quality from sub-dimensions."""
    score = 0

    # Coverage
    if pair_count >= 50:
        score += 2
    elif pair_count >= 10:
        score += 1

    # Venue breadth
    if venue_count >= 15:
        score += 2
    elif venue_count >= 5:
        score += 1

    # Freshness
    if freshness_state == FreshnessState.FRESH.value:
        score += 2
    elif freshness_state == FreshnessState.AGING.value:
        score += 1

    # Price samples
    if price_sample_size >= 20:
        score += 1

    # Contradictions penalty
    if has_contradictions:
        score -= 1

    if score >= 5:
        return EvidenceQuality.SUFFICIENT
    if score >= 2:
        return EvidenceQuality.LIMITED
    return EvidenceQuality.INSUFFICIENT


# ── Trade Reality ─────────────────────────────────────────────────

def assess_tradability(
    trade_size_usd: float,
    side: str,
    total_observed_volume: float | None,
    concentration_top5: float | None,
    venue_top1_share: float | None,
    price_agreement_state: str,
    freshness_state: str,
    pair_count: int,
) -> tuple[TradabilityState, list[TradeRealityDimension]]:
    """Assess structural tradability for a given trade size.

    This is a STRUCTURAL assessment, not an execution quote.
    """
    dims: list[TradeRealityDimension] = []

    # Market coverage assessment
    if pair_count >= 50:
        coverage_state = "HIGH"
    elif pair_count >= 15:
        coverage_state = "MODERATE"
    elif pair_count >= 3:
        coverage_state = "LOW"
    else:
        coverage_state = "INSUFFICIENT_EVIDENCE"
    dims.append(TradeRealityDimension(
        name="Market Coverage",
        state=coverage_state,
        value=float(pair_count),
        display_value=f"{pair_count} observed pairs",
    ))

    # Volume capacity assessment
    if total_observed_volume and total_observed_volume > 0:
        trade_ratio = trade_size_usd / total_observed_volume
        if trade_ratio < 0.001:
            vol_state = "HIGH"
        elif trade_ratio < 0.01:
            vol_state = "MODERATE"
        elif trade_ratio < 0.05:
            vol_state = "LOW"
        else:
            vol_state = "CONSTRAINED"
        dims.append(TradeRealityDimension(
            name="Volume Capacity",
            state=vol_state,
            value=trade_ratio,
            display_value=f"Trade is {_pct(trade_ratio)} of observed 24h volume",
        ))
    else:
        dims.append(TradeRealityDimension(
            name="Volume Capacity",
            state="INSUFFICIENT_EVIDENCE",
        ))

    # Volume concentration
    if concentration_top5 is not None:
        if concentration_top5 >= 0.80:
            conc_state = "HIGH"
        elif concentration_top5 >= 0.50:
            conc_state = "MEDIUM"
        else:
            conc_state = "LOW"
        dims.append(TradeRealityDimension(
            name="Volume Concentration",
            state=conc_state,
            value=concentration_top5,
            display_value=_pct(concentration_top5),
        ))
    else:
        dims.append(TradeRealityDimension(
            name="Volume Concentration",
            state="INSUFFICIENT_EVIDENCE",
        ))

    # Venue dependence
    if venue_top1_share is not None:
        if venue_top1_share >= 0.50:
            venue_state = "HIGH"
        elif venue_top1_share >= 0.25:
            venue_state = "MEDIUM"
        else:
            venue_state = "LOW"
        dims.append(TradeRealityDimension(
            name="Venue Dependence",
            state=venue_state,
            value=venue_top1_share,
            display_value=_pct(venue_top1_share),
        ))
    else:
        dims.append(TradeRealityDimension(
            name="Venue Dependence",
            state="INSUFFICIENT_EVIDENCE",
        ))

    # Price agreement
    dims.append(TradeRealityDimension(
        name="Price Agreement",
        state=price_agreement_state,
    ))

    # Freshness
    dims.append(TradeRealityDimension(
        name="Freshness",
        state=freshness_state,
    ))

    # Determine overall tradability
    states = [d.state for d in dims]
    insufficient_count = states.count("INSUFFICIENT_EVIDENCE")

    # Check for concerning states in specific dimensions
    concerning_dims = {d.name: d.state for d in dims}
    has_concerning = (
        concerning_dims.get("Volume Concentration") in ("HIGH",)
        or concerning_dims.get("Venue Dependence") in ("HIGH",)
        or concerning_dims.get("Volume Capacity") in ("CONSTRAINED",)
        or concerning_dims.get("Price Agreement") in ("INCONSISTENT", "LOW_AGREEMENT")
        or concerning_dims.get("Freshness") in ("STALE",)
    )

    if insufficient_count >= 3:
        result = TradabilityState.INSUFFICIENT_EVIDENCE
    elif has_concerning:
        result = TradabilityState.CONDITIONAL
    elif insufficient_count > 0:
        result = TradabilityState.CONDITIONAL
    else:
        result = TradabilityState.STRUCTURALLY_SUPPORTED

    return result, dims


# ── Stress Lab ────────────────────────────────────────────────────

PREDEFINED_SCENARIOS = [
    StressScenario(
        id="STRESS-001",
        name="Top Venue Unavailable",
        description="Remove the largest venue by volume from the observed market structure.",
        parameter="remove_top_venue",
        value=1,
    ),
    StressScenario(
        id="STRESS-002",
        name="Top 5 Markets Unavailable",
        description="Remove the top 5 market pairs by volume.",
        parameter="remove_top_pairs",
        value=5,
    ),
    StressScenario(
        id="STRESS-003",
        name="Volume Concentration +25%",
        description="Simulate 25% increase in volume concentration.",
        parameter="increase_concentration",
        value=0.25,
    ),
    StressScenario(
        id="STRESS-004",
        name="Market Coverage -30%",
        description="Remove 30% of observed market pairs.",
        parameter="reduce_coverage",
        value=0.30,
    ),
    StressScenario(
        id="STRESS-005",
        name="Price Dispersion ×2",
        description="Double the observed price dispersion.",
        parameter="multiply_dispersion",
        value=2.0,
    ),
    StressScenario(
        id="STRESS-006",
        name="-10% Market Shock",
        description="Apply a 10% negative price shock across all pairs.",
        parameter="price_shock",
        value=-0.10,
    ),
    StressScenario(
        id="STRESS-007",
        name="-20% Market Shock",
        description="Apply a 20% negative price shock across all pairs.",
        parameter="price_shock",
        value=-0.20,
    ),
]


def apply_stress_scenario(
    scenario: StressScenario,
    pairs: list[MarketPair],
    venues: list[Venue],
) -> tuple[list[MarketPair], list[Venue]]:
    """Apply a stress scenario to market pairs and venues.

    Returns modified copies of pairs and venues.
    """
    stressed_pairs = [p.model_copy() for p in pairs]
    stressed_venues = [v.model_copy() for v in venues]

    param = scenario.parameter
    val = scenario.value or 0

    if param == "remove_top_venue" and stressed_venues:
        top_venue = stressed_venues[0].name
        stressed_pairs = [p for p in stressed_pairs if p.exchange_name != top_venue]
        stressed_venues = stressed_venues[1:]

    elif param == "remove_top_pairs":
        n = int(val)
        # Sort by volume desc, remove top N
        stressed_pairs.sort(
            key=lambda p: p.volume_24h_usd or 0, reverse=True
        )
        stressed_pairs = stressed_pairs[n:]
        stressed_venues = aggregate_venues_from_pairs(stressed_pairs)

    elif param == "reduce_coverage":
        # Remove val% of pairs from the bottom
        remove_count = int(len(stressed_pairs) * val)
        if remove_count > 0:
            stressed_pairs.sort(key=lambda p: p.volume_24h_usd or 0)
            stressed_pairs = stressed_pairs[remove_count:]
            stressed_venues = aggregate_venues_from_pairs(stressed_pairs)

    elif param == "price_shock":
        for p in stressed_pairs:
            if p.price_usd is not None:
                p.price_usd = p.price_usd * (1 + val)

    elif param == "increase_concentration":
        # Boost top 5 pair volumes by val%
        stressed_pairs.sort(
            key=lambda p: p.volume_24h_usd or 0, reverse=True
        )
        for p in stressed_pairs[:5]:
            if p.volume_24h_usd is not None:
                p.volume_24h_usd *= (1 + val)
        stressed_venues = aggregate_venues_from_pairs(stressed_pairs)

    elif param == "multiply_dispersion":
        # Widen price spread from median
        prices = [p.price_usd for p in stressed_pairs if p.price_usd is not None and p.price_usd > 0]
        if prices:
            median = statistics.median(prices)
            for p in stressed_pairs:
                if p.price_usd is not None and p.price_usd > 0:
                    deviation = p.price_usd - median
                    p.price_usd = median + (deviation * val)

    return stressed_pairs, stressed_venues


def aggregate_venues_from_pairs(pairs: list[MarketPair]) -> list[Venue]:
    """Re-aggregate venues from a list of pairs (e.g. after stress modification)."""
    return aggregate_venues(pairs)


# ── Full Reality Report Builder ───────────────────────────────────

def build_reality_report(
    symbol: str,
    quote_data: dict,
    pairs_data: dict,
    identity_data: dict | None = None,
    global_data: dict | None = None,
) -> RealityReport:
    """Build a complete Reality Report from raw CMC data.

    This is the main entry point for the deterministic analysis pipeline.
    """
    ev = EvidenceCounter()
    evidence_list: list[Evidence] = []
    endpoints_used: list[str] = []

    # ── Asset identity ───────────────────────────────────────────
    asset_info = None
    if identity_data:
        asset_info = Asset(
            symbol=symbol,
            name=identity_data.get("name"),
            slug=identity_data.get("slug"),
            cmc_id=identity_data.get("id"),
            cmc_rank=identity_data.get("rank"),
            is_active=identity_data.get("is_active", 1) == 1,
        )
        endpoints_used.append("/v1/cryptocurrency/map")

    # ── Quote extraction ─────────────────────────────────────────
    # Handle multiple response shapes:
    #   1. Coin object directly (from get_quotes_by_id): {"id":5426,"quote":{"USD":{...}}}
    #   2. Symbol-keyed list: {"SOL": [{"quote":{"USD":{...}}}]}
    #   3. ID-keyed dict: {"5426": {"quote":{"USD":{...}}}}
    quote = {}
    if isinstance(quote_data, dict):
        # Shape 1: coin object directly (has top-level "quote" key)
        if "quote" in quote_data and isinstance(quote_data.get("quote"), dict):
            quote = quote_data
        else:
            # Shape 2: symbol-keyed
            items = quote_data.get(symbol, [])
            if isinstance(items, list) and items:
                quote = items[0]
            elif isinstance(items, dict) and "quote" in items:
                quote = items
            # Shape 3: scan all values for a coin object
            if not quote:
                for v in quote_data.values():
                    if isinstance(v, list) and v and isinstance(v[0], dict) and "quote" in v[0]:
                        quote = v[0]
                        break
                    elif isinstance(v, dict) and "quote" in v:
                        quote = v
                        break

    market_quote = (quote.get("quote") or {}).get("USD", {})
    price = _safe_float(market_quote.get("price"))
    volume_24h = _safe_float(market_quote.get("volume_24h"))
    market_cap = _safe_float(market_quote.get("market_cap"))
    quote_timestamp = market_quote.get("last_updated")
    # Extra fields available from CMC quotes endpoint
    cex_volume_24h = _safe_float(market_quote.get("cex_volume_24h"))
    dex_volume_24h = _safe_float(market_quote.get("dex_volume_24h"))
    pct_change_1h = _safe_float(market_quote.get("percent_change_1h"))
    pct_change_24h = _safe_float(market_quote.get("percent_change_24h"))
    pct_change_7d = _safe_float(market_quote.get("percent_change_7d"))
    market_cap_dominance = _safe_float(market_quote.get("market_cap_dominance"))
    # Fields from coin object itself
    num_market_pairs_cmc = quote.get("num_market_pairs")  # CMC's reported pair count
    circulating_supply = _safe_float(quote.get("circulating_supply"))
    cmc_rank_from_quote = quote.get("cmc_rank")

    endpoints_used.append("/v2/cryptocurrency/quotes/latest")

    eid = ev.next_id()
    evidence_list.append(Evidence(
        evidence_id=eid,
        finding="headline_price",
        value=price,
        unit="USD",
        source_endpoint="/v2/cryptocurrency/quotes/latest",
        source_timestamp=quote_timestamp,
        calculation="Direct CMC quote observation",
        limitation="Current CMC-reported price. Not a guaranteed execution price.",
    ))

    eid2 = ev.next_id()
    evidence_list.append(Evidence(
        evidence_id=eid2,
        finding="headline_volume_24h",
        value=volume_24h,
        unit="USD",
        source_endpoint="/v2/cryptocurrency/quotes/latest",
        source_timestamp=quote_timestamp,
        calculation="Direct CMC quote observation",
        limitation="CMC-reported aggregate 24h volume. Methodology may differ from per-pair sum.",
    ))

    eid3 = ev.next_id()
    evidence_list.append(Evidence(
        evidence_id=eid3,
        finding="headline_market_cap",
        value=market_cap,
        unit="USD",
        source_endpoint="/v2/cryptocurrency/quotes/latest",
        source_timestamp=quote_timestamp,
        calculation="Direct CMC quote observation",
        limitation="CMC-reported market cap based on circulating supply.",
    ))

    # ── Market pair normalization ────────────────────────────────
    raw_pairs = pairs_data.get("market_pairs", [])
    if not isinstance(raw_pairs, list):
        raw_pairs = []

    pairs = normalize_market_pairs(raw_pairs)
    endpoints_used.append("/v2/cryptocurrency/market-pairs/latest")

    eid4 = ev.next_id()
    evidence_list.append(Evidence(
        evidence_id=eid4,
        finding="observed_market_pairs",
        value=len(pairs),
        unit="pairs",
        source_endpoint="/v2/cryptocurrency/market-pairs/latest",
        calculation="Count of returned market pairs",
        sample_size=len(pairs),
        limitation="Limited to pairs returned by CMC API (max 500 per request).",
    ))

    # ── Volume analysis ──────────────────────────────────────────
    pair_volumes = [
        p.volume_24h_usd for p in pairs
        if p.volume_24h_usd is not None and p.volume_24h_usd > 0
    ]
    total_observed_volume = sum(pair_volumes)

    # Top-1, Top-5, Top-10 concentration
    conc_1 = calc_volume_concentration(pair_volumes, 1)
    conc_5 = calc_volume_concentration(pair_volumes, 5)
    conc_10 = calc_volume_concentration(pair_volumes, 10)

    eid5 = ev.next_id()
    evidence_list.append(Evidence(
        evidence_id=eid5,
        finding="total_observed_volume",
        value=total_observed_volume,
        unit="USD",
        source_endpoint="/v2/cryptocurrency/market-pairs/latest",
        calculation="sum(volume_24h_usd) across all returned pairs with volume > 0",
        sample_size=len(pair_volumes),
        limitation="Sum of CMC-reported pair volumes. May differ from headline aggregate.",
    ))

    eid6 = ev.next_id()
    evidence_list.append(Evidence(
        evidence_id=eid6,
        finding="top_1_volume_concentration",
        value=conc_1,
        unit="ratio",
        source_endpoint="/v2/cryptocurrency/market-pairs/latest",
        calculation="volume of top 1 pair / total observed pair volume",
        sample_size=len(pair_volumes),
        limitation="Concentration calculated over returned pairs only.",
    ))

    eid7 = ev.next_id()
    evidence_list.append(Evidence(
        evidence_id=eid7,
        finding="top_5_volume_concentration",
        value=conc_5,
        unit="ratio",
        source_endpoint="/v2/cryptocurrency/market-pairs/latest",
        calculation="sum(top 5 pair volumes) / total observed pair volume",
        sample_size=len(pair_volumes),
        limitation="Concentration calculated over returned pairs only.",
    ))

    eid8 = ev.next_id()
    evidence_list.append(Evidence(
        evidence_id=eid8,
        finding="top_10_volume_concentration",
        value=conc_10,
        unit="ratio",
        source_endpoint="/v2/cryptocurrency/market-pairs/latest",
        calculation="sum(top 10 pair volumes) / total observed pair volume",
        sample_size=len(pair_volumes),
        limitation="Concentration calculated over returned pairs only.",
    ))

    # ── Venue analysis ───────────────────────────────────────────
    venues = aggregate_venues(pairs)
    venue_conc = calc_venue_concentration(venues)
    venue_top1 = venue_conc["top1"]

    eid9 = ev.next_id()
    evidence_list.append(Evidence(
        evidence_id=eid9,
        finding="venue_count",
        value=len(venues),
        unit="venues",
        source_endpoint="/v2/cryptocurrency/market-pairs/latest",
        calculation="Count of unique exchange names in returned pairs",
        sample_size=len(pairs),
        limitation="Venues derived from CMC-returned pairs.",
    ))

    eid10 = ev.next_id()
    evidence_list.append(Evidence(
        evidence_id=eid10,
        finding="venue_top1_concentration",
        value=venue_top1,
        unit="ratio",
        source_endpoint="/v2/cryptocurrency/market-pairs/latest",
        calculation="volume of top 1 venue / total observed pair volume",
        sample_size=len(venues),
        limitation="Venue concentration over returned pairs only.",
    ))

    # ── Price agreement ──────────────────────────────────────────
    prices = [
        p.price_usd for p in pairs
        if p.price_usd is not None and p.price_usd > 0
    ]
    price_agreement = calc_price_agreement(prices)

    eid11 = ev.next_id()
    evidence_list.append(Evidence(
        evidence_id=eid11,
        finding="price_agreement",
        value=price_agreement["dispersion_pct"],
        unit="percent",
        source_endpoint="/v2/cryptocurrency/market-pairs/latest",
        calculation=(
            f"(max - min) / median × 100 across {price_agreement['sample_size']} observed prices"
        ),
        sample_size=price_agreement["sample_size"],
        inputs=[
            f"median={price_agreement['median']}",
            f"min={price_agreement['min']}",
            f"max={price_agreement['max']}",
        ],
        limitation="Price agreement across CMC-returned pairs. Does not include all global venues.",
    ))

    # ── Freshness ────────────────────────────────────────────────
    timestamps = [p.last_updated for p in pairs]
    freshness = calc_freshness(timestamps)

    eid12 = ev.next_id()
    evidence_list.append(Evidence(
        evidence_id=eid12,
        finding="data_freshness",
        value=freshness["median_age_seconds"],
        unit="seconds",
        source_endpoint="/v2/cryptocurrency/market-pairs/latest",
        calculation="Median age of pair last_updated timestamps",
        sample_size=len(timestamps),
        limitation="Freshness based on CMC-reported update timestamps.",
    ))

    # ── Coverage ─────────────────────────────────────────────────
    coverage_state = calc_coverage_state(len(pairs), len(venues))

    # ── Contradictions ───────────────────────────────────────────
    contradictions = detect_contradictions(
        headline_volume=volume_24h,
        observed_volume=total_observed_volume,
        concentration_top5=conc_5,
        price_dispersion_pct=price_agreement["dispersion_pct"],
        pair_count=len(pairs),
        venue_count=len(venues),
        freshness_state=freshness["state"],
    )

    for i, c in enumerate(contradictions):
        eid_c = ev.next_id()
        evidence_list.append(Evidence(
            evidence_id=eid_c,
            finding=f"contradiction_{c['type']}",
            value=c["severity"],
            source_endpoint="derived",
            calculation=c["description"],
            limitation="Contradiction detected from observed data patterns.",
        ))

    # ── Evidence quality ─────────────────────────────────────────
    evidence_quality = calc_evidence_quality(
        pair_count=len(pairs),
        venue_count=len(venues),
        freshness_state=freshness["state"],
        price_sample_size=price_agreement["sample_size"],
        has_contradictions=len(contradictions) > 0,
    )

    # ── Reality Gap ──────────────────────────────────────────────
    reality_gap = RealityGap(
        headline_volume_24h=volume_24h,
        headline_market_cap=market_cap,
        headline_price=price,
        observed_pair_count=len(pairs),
        observed_total_volume=total_observed_volume,
        top5_concentration=conc_5,
        top1_venue_share=venue_top1,
        price_dispersion_pct=price_agreement["dispersion_pct"],
        coverage_state=coverage_state,
        # Enriched quote fields
        cex_volume_24h=cex_volume_24h,
        dex_volume_24h=dex_volume_24h,
        pct_change_1h=pct_change_1h,
        pct_change_24h=pct_change_24h,
        pct_change_7d=pct_change_7d,
        market_cap_dominance=market_cap_dominance,
        num_market_pairs_cmc=num_market_pairs_cmc,
        circulating_supply=circulating_supply,
    )

    # ── Concentration state ──────────────────────────────────────
    if conc_5 is None:
        concentration_state = RealityState.INSUFFICIENT_EVIDENCE.value
    elif conc_5 >= 0.70:
        concentration_state = RealityState.CONCENTRATED.value
    elif conc_5 >= 0.50:
        concentration_state = RealityState.PARTIALLY_REPRESENTATIVE.value
    else:
        concentration_state = RealityState.REPRESENTATIVE.value

    # ── Venue dependence state ───────────────────────────────────
    if venue_top1 is None:
        venue_state = RealityState.INSUFFICIENT_EVIDENCE.value
    elif venue_top1 >= 0.50:
        venue_state = RealityState.CONCENTRATED.value
    elif venue_top1 >= 0.25:
        venue_state = RealityState.PARTIALLY_REPRESENTATIVE.value
    else:
        venue_state = RealityState.REPRESENTATIVE.value

    # ── Build dimensions ─────────────────────────────────────────
    dimensions = [
        RealityDimension(
            name="Price Agreement",
            state=price_agreement["state"],
            value=price_agreement["dispersion_pct"],
            display_value=f"{price_agreement['dispersion_pct']:.2f}% dispersion" if price_agreement["dispersion_pct"] is not None else "N/A",
            evidence_ids=[eid11],
            description=f"Observed across {price_agreement['sample_size']} market prices",
        ),
        RealityDimension(
            name="Volume Concentration",
            state=concentration_state,
            value=conc_5,
            display_value=_pct(conc_5),
            evidence_ids=[eid7],
            description=f"Top 5 of {len(pair_volumes)} pairs with volume",
        ),
        RealityDimension(
            name="Venue Dependence",
            state=venue_state,
            value=venue_top1,
            display_value=f"{venues[0].name}: {_pct(venue_top1)}" if venues and venue_top1 else "N/A",
            evidence_ids=[eid10],
            description=f"Largest venue of {len(venues)} observed",
        ),
        RealityDimension(
            name="Market Coverage",
            state=coverage_state,
            value=float(len(pairs)),
            display_value=f"{len(pairs)} pairs / {len(venues)} venues",
            evidence_ids=[eid4, eid9],
            description="CMC-observed market pair coverage",
        ),
        RealityDimension(
            name="Data Freshness",
            state=freshness["state"],
            value=freshness["median_age_seconds"],
            display_value=_format_age(freshness["median_age_seconds"]),
            evidence_ids=[eid12],
            description="Median age of pair update timestamps",
        ),
        RealityDimension(
            name="Cross-Market Consistency",
            state="CONSISTENT" if not contradictions else "INCONSISTENT",
            value=float(len(contradictions)),
            display_value=f"{len(contradictions)} contradiction(s)" if contradictions else "No contradictions detected",
            evidence_ids=[e.evidence_id for e in evidence_list if e.finding.startswith("contradiction_")],
            description="Structural contradictions in observed data",
        ),
        RealityDimension(
            name="Evidence Completeness",
            state=evidence_quality.value,
            value=None,
            display_value=evidence_quality.value,
            evidence_ids=[],
            description="Overall assessment of evidence coverage, freshness, and consistency",
        ),
    ]

    # ── Global context ───────────────────────────────────────────
    global_context = None
    if global_data:
        usd_quote = (global_data.get("quote") or {}).get("USD", {})
        global_context = GlobalMarketContext(
            total_market_cap_usd=_safe_float(usd_quote.get("total_market_cap")),
            total_volume_24h_usd=_safe_float(usd_quote.get("total_volume_24h")),
            btc_dominance=_safe_float(global_data.get("btc_dominance")),
            eth_dominance=_safe_float(global_data.get("eth_dominance")),
            active_cryptocurrencies=global_data.get("active_cryptocurrencies"),
            active_exchanges=global_data.get("active_exchanges"),
            total_market_pairs=global_data.get("total_market_pairs"),
            last_updated=usd_quote.get("last_updated"),
        )
        endpoints_used.append("/v1/global-metrics/quotes/latest")

    # ── Limitations ──────────────────────────────────────────────
    limitations = [
        "This analysis covers CMC-tracked market observations returned by the API.",
        "Market pair data is limited to the first 500 pairs returned.",
        "Structural tradability is not an execution quote or guarantee.",
        "CMC-reported volumes may use varying methodologies across exchanges.",
        "Price agreement is across observed pairs only, not all global venues.",
    ]
    if contradictions:
        limitations.append(
            f"{len(contradictions)} structural contradiction(s) detected in observed data."
        )

    # ── Overall status ───────────────────────────────────────────
    has_price = price is not None
    if not pairs and has_price:
        # We have headline data but no structural pair data (e.g. free plan)
        status = "QUOTE_ONLY"
    elif not pairs:
        status = "INSUFFICIENT_EVIDENCE"
    elif evidence_quality == EvidenceQuality.SUFFICIENT:
        status = "EVIDENCE_READY"
    elif evidence_quality == EvidenceQuality.LIMITED:
        status = "LIMITED_EVIDENCE"
    else:
        status = "INSUFFICIENT_EVIDENCE"

    # Top 10 pairs for the sample
    pairs_sorted = sorted(pairs, key=lambda p: p.volume_24h_usd or 0, reverse=True)

    return RealityReport(
        asset=symbol,
        asset_info=asset_info,
        status=status,
        observation_timestamp=_now_iso(),
        dimensions=dimensions,
        reality_gap=reality_gap,
        venues=venues[:20],  # Top 20 venues
        market_pairs_sample=pairs_sorted[:15],  # Top 15 pairs
        evidence=evidence_list,
        global_context=global_context,
        limitations=limitations,
        cmc_endpoints_used=list(set(endpoints_used)),
    )


def _format_age(seconds: float | None) -> str:
    """Format an age in seconds to a human-readable string."""
    if seconds is None:
        return "N/A"
    if seconds < 60:
        return f"{seconds:.0f}s ago"
    if seconds < 3600:
        return f"{seconds / 60:.0f}m ago"
    return f"{seconds / 3600:.1f}h ago"
