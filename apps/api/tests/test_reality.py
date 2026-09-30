"""Comprehensive tests for the MarketReality Reality Engine.

Tests cover:
- Data normalization and edge cases
- Volume concentration calculations
- Venue concentration
- Price agreement
- Freshness detection
- Coverage classification
- Contradiction detection
- Evidence quality assessment
- Trade reality assessment
- Stress scenario application
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.models import MarketPair, MarketType, Venue, EvidenceQuality, TradabilityState
from app.reality import (
    _safe_float,
    normalize_market_pairs,
    aggregate_venues,
    calc_volume_concentration,
    calc_venue_concentration,
    calc_price_agreement,
    calc_freshness,
    calc_coverage_state,
    detect_contradictions,
    calc_evidence_quality,
    assess_tradability,
    apply_stress_scenario,
    build_reality_report,
    PREDEFINED_SCENARIOS,
)


# ── Helpers ───────────────────────────────────────────────────────

def _make_pair(
    exchange: str = "TestExchange",
    volume: float = 1000.0,
    price: float = 100.0,
    pair: str = "BTC/USD",
    category: str = "spot",
) -> dict:
    """Create a raw CMC market pair dict."""
    return {
        "exchange": {"name": exchange, "slug": exchange.lower(), "id": 1},
        "market_pair": pair,
        "category": category,
        "market_pair_base": {"currency_symbol": "BTC"},
        "market_pair_quote": {"currency_symbol": "USD"},
        "quote": {
            "USD": {
                "price": price,
                "volume_24h": volume,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        },
    }


# ── safe_float ────────────────────────────────────────────────────

class TestSafeFloat:
    def test_valid_float(self):
        assert _safe_float(42.5) == 42.5

    def test_valid_int(self):
        assert _safe_float(42) == 42.0

    def test_string_number(self):
        assert _safe_float("3.14") == 3.14

    def test_none(self):
        assert _safe_float(None) is None

    def test_invalid_string(self):
        assert _safe_float("not_a_number") is None

    def test_empty_string(self):
        assert _safe_float("") is None


# ── Market pair normalization ─────────────────────────────────────

class TestNormalizePairs:
    def test_basic_normalization(self):
        raw = [_make_pair(volume=500, price=50)]
        pairs = normalize_market_pairs(raw)
        assert len(pairs) == 1
        assert pairs[0].exchange_name == "TestExchange"
        assert pairs[0].volume_24h_usd == 500.0
        assert pairs[0].price_usd == 50.0

    def test_empty_input(self):
        assert normalize_market_pairs([]) == []

    def test_non_dict_items_skipped(self):
        pairs = normalize_market_pairs([None, "bad", 42])
        assert len(pairs) == 0

    def test_missing_exchange(self):
        raw = [{"quote": {"USD": {"volume_24h": 100, "price": 10}}}]
        pairs = normalize_market_pairs(raw)
        assert len(pairs) == 1
        assert pairs[0].exchange_name == "Unknown"

    def test_null_volume(self):
        raw = [_make_pair()]
        raw[0]["quote"]["USD"]["volume_24h"] = None
        pairs = normalize_market_pairs(raw)
        assert pairs[0].volume_24h_usd is None

    def test_zero_volume(self):
        raw = [_make_pair(volume=0)]
        pairs = normalize_market_pairs(raw)
        assert pairs[0].volume_24h_usd == 0.0

    def test_null_price(self):
        raw = [_make_pair()]
        raw[0]["quote"]["USD"]["price"] = None
        pairs = normalize_market_pairs(raw)
        assert pairs[0].price_usd is None


# ── Volume concentration ─────────────────────────────────────────

class TestVolumeConcentration:
    def test_top5_basic(self):
        volumes = [700, 100, 50, 50, 50, 50]
        result = calc_volume_concentration(volumes, 5)
        # top 5 = 700+100+50+50+50 = 950, total = 1000
        assert result == 0.95

    def test_top1(self):
        volumes = [700, 100, 50, 50, 50, 50]
        result = calc_volume_concentration(volumes, 1)
        assert result == 0.7

    def test_top10_fewer_than_10(self):
        volumes = [100, 50, 50]
        result = calc_volume_concentration(volumes, 10)
        # All included
        assert result == 1.0

    def test_empty_list(self):
        assert calc_volume_concentration([], 5) is None

    def test_zero_total(self):
        assert calc_volume_concentration([0, 0, 0], 5) is None

    def test_single_market(self):
        assert calc_volume_concentration([1000], 5) == 1.0

    def test_original_starter_test(self):
        """The original test_concentration_is_deterministic from the starter."""
        data = {
            "quotes": {
                "data": {
                    "BTC": [{"quote": {"USD": {"price": 100.0, "volume_24h": 1000.0}}}]
                }
            },
            "pairs": {
                "data": {
                    "market_pairs": [
                        {"quote": {"USD": {"volume_24h": 700}}},
                        {"quote": {"USD": {"volume_24h": 100}}},
                        {"quote": {"USD": {"volume_24h": 50}}},
                        {"quote": {"USD": {"volume_24h": 50}}},
                        {"quote": {"USD": {"volume_24h": 50}}},
                        {"quote": {"USD": {"volume_24h": 50}}},
                    ]
                }
            },
        }
        # Use the new build_reality_report interface
        report = build_reality_report(
            "BTC",
            quote_data=data["quotes"].get("data", {}),
            pairs_data=data["pairs"].get("data", {}),
        )
        conc_dim = next(
            (d for d in report.dimensions if d.name == "Volume Concentration"), None
        )
        assert conc_dim is not None
        # 700+100+50+50+50 = 950 / 1000 = 0.95 (top 5)
        assert conc_dim.value == 0.95


# ── Venue concentration ──────────────────────────────────────────

class TestVenueConcentration:
    def test_basic(self):
        venues = [
            Venue(name="A", total_volume_24h_usd=600, pair_count=5, volume_share=0.6),
            Venue(name="B", total_volume_24h_usd=300, pair_count=3, volume_share=0.3),
            Venue(name="C", total_volume_24h_usd=100, pair_count=2, volume_share=0.1),
        ]
        result = calc_venue_concentration(venues)
        assert result["top1"] == 0.6
        assert result["top5"] == 1.0

    def test_empty(self):
        result = calc_venue_concentration([])
        assert result["top1"] is None

    def test_single_venue(self):
        venues = [Venue(name="A", total_volume_24h_usd=1000, pair_count=1, volume_share=1.0)]
        result = calc_venue_concentration(venues)
        assert result["top1"] == 1.0


# ── Price agreement ───────────────────────────────────────────────

class TestPriceAgreement:
    def test_tight_prices(self):
        prices = [100.0, 100.1, 99.9, 100.05, 99.95]
        result = calc_price_agreement(prices)
        assert result["state"] == "HIGH_AGREEMENT"
        assert result["sample_size"] == 5
        assert result["dispersion_pct"] < 0.5

    def test_moderate_prices(self):
        prices = [100.0, 101.0, 99.0, 100.5]
        result = calc_price_agreement(prices)
        assert result["state"] == "MODERATE_AGREEMENT"

    def test_wide_prices(self):
        prices = [100.0, 110.0, 90.0]
        result = calc_price_agreement(prices)
        assert result["state"] in ("LOW_AGREEMENT", "INCONSISTENT")

    def test_empty(self):
        result = calc_price_agreement([])
        assert result["state"] == "INSUFFICIENT_EVIDENCE"

    def test_single_price(self):
        result = calc_price_agreement([100.0])
        assert result["state"] == "SINGLE_SOURCE"

    def test_outlier_detection(self):
        prices = [100.0, 100.1, 100.2, 150.0]  # 150 is an outlier
        result = calc_price_agreement(prices)
        assert result["outlier_count"] >= 1


# ── Freshness ─────────────────────────────────────────────────────

class TestFreshness:
    def test_fresh_data(self):
        now = datetime.now(timezone.utc)
        timestamps = [
            (now - timedelta(seconds=30)).isoformat(),
            (now - timedelta(seconds=60)).isoformat(),
        ]
        result = calc_freshness(timestamps)
        assert result["state"] == "FRESH"

    def test_stale_data(self):
        now = datetime.now(timezone.utc)
        timestamps = [
            (now - timedelta(hours=2)).isoformat(),
            (now - timedelta(hours=3)).isoformat(),
        ]
        result = calc_freshness(timestamps)
        assert result["state"] == "STALE"

    def test_no_timestamps(self):
        result = calc_freshness([])
        assert result["state"] == "UNKNOWN"

    def test_null_timestamps(self):
        result = calc_freshness([None, None])
        assert result["state"] == "UNKNOWN"


# ── Coverage state ────────────────────────────────────────────────

class TestCoverageState:
    def test_high(self):
        assert calc_coverage_state(150, 25) == "HIGH"

    def test_moderate(self):
        assert calc_coverage_state(50, 15) == "MODERATE"

    def test_low(self):
        assert calc_coverage_state(10, 3) == "LOW"

    def test_minimal(self):
        assert calc_coverage_state(3, 2) == "MINIMAL"

    def test_zero(self):
        assert calc_coverage_state(0, 0) == "INSUFFICIENT_EVIDENCE"


# ── Contradiction detection ───────────────────────────────────────

class TestContradictions:
    def test_no_contradictions(self):
        result = detect_contradictions(
            headline_volume=1_000_000,
            observed_volume=800_000,
            concentration_top5=0.4,
            price_dispersion_pct=0.3,
            pair_count=50,
            venue_count=15,
            freshness_state="FRESH",
        )
        assert len(result) == 0

    def test_volume_coverage_mismatch(self):
        result = detect_contradictions(
            headline_volume=5_000_000_000,
            observed_volume=4_000_000_000,
            concentration_top5=0.4,
            price_dispersion_pct=0.3,
            pair_count=5,
            venue_count=3,
            freshness_state="FRESH",
        )
        assert any(c["type"] == "volume_coverage_mismatch" for c in result)

    def test_price_divergence(self):
        result = detect_contradictions(
            headline_volume=1_000_000,
            observed_volume=800_000,
            concentration_top5=0.4,
            price_dispersion_pct=10.0,
            pair_count=50,
            venue_count=15,
            freshness_state="FRESH",
        )
        assert any(c["type"] == "price_divergence" for c in result)

    def test_stale_data_contradiction(self):
        result = detect_contradictions(
            headline_volume=1_000_000,
            observed_volume=800_000,
            concentration_top5=0.4,
            price_dispersion_pct=0.3,
            pair_count=50,
            venue_count=15,
            freshness_state="STALE",
        )
        assert any(c["type"] == "stale_data" for c in result)


# ── Evidence quality ──────────────────────────────────────────────

class TestEvidenceQuality:
    def test_sufficient(self):
        result = calc_evidence_quality(
            pair_count=100,
            venue_count=20,
            freshness_state="FRESH",
            price_sample_size=50,
            has_contradictions=False,
        )
        assert result == EvidenceQuality.SUFFICIENT

    def test_limited(self):
        result = calc_evidence_quality(
            pair_count=20,
            venue_count=8,
            freshness_state="AGING",
            price_sample_size=10,
            has_contradictions=False,
        )
        assert result == EvidenceQuality.LIMITED

    def test_insufficient(self):
        result = calc_evidence_quality(
            pair_count=2,
            venue_count=1,
            freshness_state="STALE",
            price_sample_size=1,
            has_contradictions=True,
        )
        assert result == EvidenceQuality.INSUFFICIENT


# ── Trade reality ─────────────────────────────────────────────────

class TestTradeReality:
    def test_structurally_supported(self):
        result, dims = assess_tradability(
            trade_size_usd=10_000,
            side="BUY",
            total_observed_volume=100_000_000,
            concentration_top5=0.3,
            venue_top1_share=0.15,
            price_agreement_state="HIGH_AGREEMENT",
            freshness_state="FRESH",
            pair_count=100,
        )
        assert result == TradabilityState.STRUCTURALLY_SUPPORTED

    def test_constrained(self):
        result, dims = assess_tradability(
            trade_size_usd=10_000_000,
            side="BUY",
            total_observed_volume=5_000_000,
            concentration_top5=0.9,
            venue_top1_share=0.7,
            price_agreement_state="INCONSISTENT",
            freshness_state="STALE",
            pair_count=5,
        )
        assert result in (TradabilityState.CONDITIONAL, TradabilityState.CONSTRAINED)

    def test_insufficient_evidence(self):
        result, dims = assess_tradability(
            trade_size_usd=100_000,
            side="BUY",
            total_observed_volume=None,
            concentration_top5=None,
            venue_top1_share=None,
            price_agreement_state="INSUFFICIENT_EVIDENCE",
            freshness_state="UNKNOWN",
            pair_count=0,
        )
        assert result == TradabilityState.INSUFFICIENT_EVIDENCE


# ── Stress scenarios ──────────────────────────────────────────────

class TestStressScenarios:
    def _make_pairs_and_venues(self):
        pairs = [
            MarketPair(
                exchange_name="Binance", market_pair="BTC/USD",
                volume_24h_usd=5000, price_usd=100,
            ),
            MarketPair(
                exchange_name="Coinbase", market_pair="BTC/USD",
                volume_24h_usd=3000, price_usd=100,
            ),
            MarketPair(
                exchange_name="Kraken", market_pair="BTC/EUR",
                volume_24h_usd=2000, price_usd=100.5,
            ),
        ]
        venues = aggregate_venues(pairs)
        return pairs, venues

    def test_remove_top_venue(self):
        pairs, venues = self._make_pairs_and_venues()
        scenario = PREDEFINED_SCENARIOS[0]  # Top Venue Unavailable
        stressed_pairs, stressed_venues = apply_stress_scenario(scenario, pairs, venues)
        # Binance was top, should be removed
        assert all(p.exchange_name != "Binance" for p in stressed_pairs)
        assert len(stressed_pairs) < len(pairs)

    def test_remove_top_pairs(self):
        pairs, venues = self._make_pairs_and_venues()
        scenario = PREDEFINED_SCENARIOS[1]  # Top 5 Markets Unavailable
        stressed_pairs, _ = apply_stress_scenario(scenario, pairs, venues)
        # Only 3 pairs, remove top 5 removes all
        assert len(stressed_pairs) == 0

    def test_price_shock(self):
        pairs, venues = self._make_pairs_and_venues()
        scenario = PREDEFINED_SCENARIOS[5]  # -10% shock
        stressed_pairs, _ = apply_stress_scenario(scenario, pairs, venues)
        assert stressed_pairs[0].price_usd == pytest.approx(90.0, abs=0.01)


# ── Full report builder ──────────────────────────────────────────

class TestBuildRealityReport:
    def test_basic_report(self):
        report = build_reality_report(
            symbol="BTC",
            quote_data={
                "BTC": [{"quote": {"USD": {"price": 60000, "volume_24h": 30_000_000_000, "market_cap": 1_200_000_000_000}}}]
            },
            pairs_data={
                "market_pairs": [
                    _make_pair("Binance", 10_000_000, 60000),
                    _make_pair("Coinbase", 5_000_000, 60010),
                    _make_pair("Kraken", 3_000_000, 59990),
                    _make_pair("OKX", 2_000_000, 60005),
                    _make_pair("Bybit", 1_000_000, 60020),
                ]
            },
        )
        assert report.asset == "BTC"
        assert report.status in ("EVIDENCE_READY", "LIMITED_EVIDENCE")
        assert len(report.dimensions) == 7
        assert len(report.evidence) > 0
        assert report.reality_gap is not None
        assert report.reality_gap.headline_price == 60000

    def test_empty_pairs(self):
        report = build_reality_report(
            symbol="UNKNOWN",
            quote_data={},
            pairs_data={"market_pairs": []},
        )
        assert report.status == "INSUFFICIENT_EVIDENCE"

    def test_malformed_response(self):
        report = build_reality_report(
            symbol="BAD",
            quote_data={"BAD": "not_a_list"},
            pairs_data={"market_pairs": "not_a_list"},
        )
        assert report.status == "INSUFFICIENT_EVIDENCE"

    def test_duplicate_pairs_handled(self):
        """Duplicate pairs should be counted as separate observations."""
        report = build_reality_report(
            symbol="SOL",
            quote_data={
                "SOL": [{"quote": {"USD": {"price": 150, "volume_24h": 5_000_000}}}]
            },
            pairs_data={
                "market_pairs": [
                    _make_pair("Binance", 1000, 150, "SOL/USD"),
                    _make_pair("Binance", 1000, 150, "SOL/USD"),  # duplicate
                    _make_pair("Binance", 500, 150.1, "SOL/USDT"),
                ]
            },
        )
        pair_evidence = next(
            (e for e in report.evidence if e.finding == "observed_market_pairs"), None
        )
        assert pair_evidence is not None
        assert pair_evidence.value == 3  # All 3 counted

    def test_all_evidence_ids_unique(self):
        report = build_reality_report(
            symbol="ETH",
            quote_data={
                "ETH": [{"quote": {"USD": {"price": 3000, "volume_24h": 10_000_000}}}]
            },
            pairs_data={
                "market_pairs": [_make_pair("Binance", 5000, 3000)]
            },
        )
        ids = [e.evidence_id for e in report.evidence]
        assert len(ids) == len(set(ids)), "Evidence IDs must be unique"

    def test_evidence_has_required_fields(self):
        report = build_reality_report(
            symbol="BTC",
            quote_data={
                "BTC": [{"quote": {"USD": {"price": 60000, "volume_24h": 30_000_000_000}}}]
            },
            pairs_data={
                "market_pairs": [_make_pair("Binance", 10_000_000, 60000)]
            },
        )
        for ev in report.evidence:
            assert ev.evidence_id, "Evidence must have an ID"
            assert ev.finding, "Evidence must have a finding"
            assert ev.source_endpoint, "Evidence must have a source endpoint"
            assert ev.calculation, "Evidence must have a calculation description"
