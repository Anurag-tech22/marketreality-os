"""Demo data for MarketReality OS — realistic sample reports for hackathon demos.

These are structurally plausible values, clearly marked as DEMO.
Used when CMC API is unreachable or for UI demonstrations.
"""
from __future__ import annotations
from datetime import datetime, timezone

DEMO_REPORTS = {
    "SOL": {
        "asset": "SOL",
        "asset_info": {
            "symbol": "SOL", "name": "Solana", "slug": "solana",
            "cmc_id": 5426, "cmc_rank": 7, "is_active": True
        },
        "status": "EVIDENCE_READY",
        "observation_timestamp": None,  # filled at runtime
        "dimensions": [
            {"name": "Price Agreement", "state": "HIGH_AGREEMENT", "value": 0.18,
             "display_value": "0.18% dispersion", "evidence_ids": ["EV-001"],
             "description": "Observed across 487 market prices"},
            {"name": "Volume Concentration", "state": "CONCENTRATED", "value": 0.72,
             "display_value": "72.1% top-5", "evidence_ids": ["EV-005", "EV-006"],
             "description": "Top 5 of 487 pairs with volume"},
            {"name": "Venue Dependence", "state": "CONCENTRATED", "value": 0.41,
             "display_value": "41.2% top venue", "evidence_ids": ["EV-009", "EV-010"],
             "description": "Largest venue of 48 observed"},
            {"name": "Market Coverage", "state": "REPRESENTATIVE", "value": 487,
             "display_value": "487 pairs / 48 venues", "evidence_ids": ["EV-004"],
             "description": "CMC-observed market pair coverage"},
            {"name": "Data Freshness", "state": "FRESH", "value": 142,
             "display_value": "2.4m ago", "evidence_ids": ["EV-011"],
             "description": "Median pair data age"},
            {"name": "Cross-Market Consistency", "state": "REPRESENTATIVE", "value": 0,
             "display_value": "0 contradictions", "evidence_ids": ["EV-012"],
             "description": "Structural contradiction detection"},
            {"name": "Evidence Completeness", "state": "REPRESENTATIVE", "value": 6,
             "display_value": "Score 6/7", "evidence_ids": ["EV-013"],
             "description": "Quality assessment across dimensions"},
        ],
        "reality_gap": {
            "headline_price": 121.34,
            "headline_volume_24h": 2917301454.76,
            "headline_market_cap": 71314604538.16,
            "observed_pair_count": 487,
            "observed_total_volume": 2681429827.0,
            "top5_concentration": 0.721,
            "top1_venue_share": 0.412,
            "price_dispersion_pct": 0.18,
            "coverage_state": "REPRESENTATIVE",
            "cex_volume_24h": 2903915979.01,
            "dex_volume_24h": 13385475.75,
            "pct_change_1h": 0.108,
            "pct_change_24h": -0.41,
            "pct_change_7d": 9.37,
            "market_cap_dominance": 2.47,
            "num_market_pairs_cmc": 1181,
            "circulating_supply": 587712515.23,
        },
        "venues": [
            {"name": "Binance", "slug": "binance", "exchange_id": 270,
             "market_type": "CEX", "total_volume_24h_usd": 1104850124.0,
             "pair_count": 6, "volume_share": 0.412},
            {"name": "Coinbase Exchange", "slug": "coinbase-exchange", "exchange_id": 89,
             "market_type": "CEX", "total_volume_24h_usd": 412394481.0,
             "pair_count": 3, "volume_share": 0.154},
            {"name": "OKX", "slug": "okx", "exchange_id": 294,
             "market_type": "CEX", "total_volume_24h_usd": 347012948.0,
             "pair_count": 5, "volume_share": 0.129},
            {"name": "Bybit", "slug": "bybit", "exchange_id": 521,
             "market_type": "CEX", "total_volume_24h_usd": 223486902.0,
             "pair_count": 4, "volume_share": 0.083},
            {"name": "Kraken", "slug": "kraken", "exchange_id": 24,
             "market_type": "CEX", "total_volume_24h_usd": 134897234.0,
             "pair_count": 3, "volume_share": 0.050},
            {"name": "Raydium", "slug": "raydium", "exchange_id": 1225,
             "market_type": "DEX", "total_volume_24h_usd": 13385475.0,
             "pair_count": 18, "volume_share": 0.005},
        ],
        "evidence": [
            {"evidence_id": "EV-001", "finding": "headline_price", "value": 121.34,
             "unit": "USD", "source_endpoint": "/v2/cryptocurrency/quotes/latest",
             "source_timestamp": None, "calculation": "Direct CMC quote observation",
             "sample_size": None,
             "limitation": "Current CMC-reported price. Not a guaranteed execution price."},
            {"evidence_id": "EV-002", "finding": "headline_volume_24h", "value": 2917301454.76,
             "unit": "USD", "source_endpoint": "/v2/cryptocurrency/quotes/latest",
             "source_timestamp": None, "calculation": "Direct CMC quote observation",
             "sample_size": None,
             "limitation": "CMC-reported aggregate 24h volume. Methodology may differ from per-pair sum."},
            {"evidence_id": "EV-003", "finding": "headline_market_cap", "value": 71314604538.16,
             "unit": "USD", "source_endpoint": "/v2/cryptocurrency/quotes/latest",
             "source_timestamp": None, "calculation": "Direct CMC quote observation",
             "sample_size": None,
             "limitation": "CMC-reported market cap based on circulating supply."},
            {"evidence_id": "EV-004", "finding": "observed_market_pairs", "value": 487,
             "unit": "pairs", "source_endpoint": "/v2/cryptocurrency/market-pairs/latest",
             "source_timestamp": None, "calculation": "Count of returned market pairs",
             "sample_size": 487,
             "limitation": "Limited to pairs returned by CMC API (max 500 per request)."},
            {"evidence_id": "EV-005", "finding": "top_5_volume_concentration", "value": 0.721,
             "unit": "ratio", "source_endpoint": "/v2/cryptocurrency/market-pairs/latest",
             "calculation": "sum(top 5 pair volumes) / total observed pair volume",
             "sample_size": 487,
             "limitation": "Concentration calculated over returned pairs only."},
            {"evidence_id": "EV-006", "finding": "top_1_volume_concentration", "value": 0.412,
             "unit": "ratio", "source_endpoint": "/v2/cryptocurrency/market-pairs/latest",
             "calculation": "volume of top 1 pair / total observed pair volume",
             "sample_size": 487,
             "limitation": "Concentration calculated over returned pairs only."},
        ],
        "global_context": {
            "total_market_cap_usd": 2884222341731.94,
            "total_volume_24h_usd": 52890938593.89,
            "btc_dominance": 58.55,
            "eth_dominance": 11.37,
            "active_cryptocurrencies": 8160,
            "active_exchanges": 978,
            "total_market_pairs": None,
            "last_updated": None,
            "source_endpoint": "/v1/global-metrics/quotes/latest",
        },
        "limitations": [
            "DEMO MODE — data is structurally plausible but not live CMC data.",
            "This analysis covers CMC-tracked market observations returned by the API.",
            "Market pair data is limited to the first 500 pairs returned.",
            "Structural tradability is not an execution quote or guarantee.",
            "CMC-reported volumes may use varying methodologies across exchanges.",
        ],
        "cmc_endpoints_used": [
            "/v1/cryptocurrency/map",
            "/v2/cryptocurrency/quotes/latest",
            "/v2/cryptocurrency/market-pairs/latest",
            "/v1/global-metrics/quotes/latest",
        ],
    }
}

# Mirror SOL for BTC/ETH with adjusted values
DEMO_REPORTS["BTC"] = {
    **DEMO_REPORTS["SOL"],
    "asset": "BTC",
    "asset_info": {"symbol": "BTC", "name": "Bitcoin", "slug": "bitcoin",
                   "cmc_id": 1, "cmc_rank": 1, "is_active": True},
    "reality_gap": {
        **DEMO_REPORTS["SOL"]["reality_gap"],
        "headline_price": 63482.15,
        "headline_volume_24h": 38241983012.0,
        "headline_market_cap": 1251847293041.0,
        "observed_pair_count": 500,
        "top5_concentration": 0.542,
        "top1_venue_share": 0.298,
        "price_dispersion_pct": 0.09,
        "coverage_state": "REPRESENTATIVE",
        "cex_volume_24h": 37981234000.0,
        "dex_volume_24h": 260749012.0,
        "pct_change_1h": 0.21,
        "pct_change_24h": 1.34,
        "pct_change_7d": 5.82,
        "market_cap_dominance": 58.55,
        "num_market_pairs_cmc": 11240,
        "circulating_supply": 19720000.0,
    },
    "dimensions": [
        {"name": "Price Agreement", "state": "HIGH_AGREEMENT", "value": 0.09,
         "display_value": "0.09% dispersion", "evidence_ids": ["EV-001"],
         "description": "Observed across 500 market prices"},
        {"name": "Volume Concentration", "state": "PARTIALLY_REPRESENTATIVE", "value": 0.54,
         "display_value": "54.2% top-5", "evidence_ids": ["EV-005"],
         "description": "Top 5 of 500 pairs with volume"},
        {"name": "Venue Dependence", "state": "PARTIALLY_REPRESENTATIVE", "value": 0.30,
         "display_value": "29.8% top venue", "evidence_ids": ["EV-009"],
         "description": "Largest venue of 112 observed"},
        {"name": "Market Coverage", "state": "REPRESENTATIVE", "value": 500,
         "display_value": "500 pairs / 112 venues", "evidence_ids": ["EV-004"],
         "description": "CMC-observed market pair coverage (API cap)"},
        {"name": "Data Freshness", "state": "FRESH", "value": 87,
         "display_value": "1.5m ago", "evidence_ids": ["EV-011"],
         "description": "Median pair data age"},
        {"name": "Cross-Market Consistency", "state": "REPRESENTATIVE", "value": 0,
         "display_value": "0 contradictions", "evidence_ids": ["EV-012"],
         "description": "Structural contradiction detection"},
        {"name": "Evidence Completeness", "state": "REPRESENTATIVE", "value": 7,
         "display_value": "Score 7/7", "evidence_ids": ["EV-013"],
         "description": "Quality assessment across dimensions"},
    ],
}

DEMO_REPORTS["ETH"] = {
    **DEMO_REPORTS["SOL"],
    "asset": "ETH",
    "asset_info": {"symbol": "ETH", "name": "Ethereum", "slug": "ethereum",
                   "cmc_id": 1027, "cmc_rank": 2, "is_active": True},
    "reality_gap": {
        **DEMO_REPORTS["SOL"]["reality_gap"],
        "headline_price": 2481.76,
        "headline_volume_24h": 14827349812.0,
        "headline_market_cap": 297823948201.0,
        "observed_pair_count": 500,
        "top5_concentration": 0.612,
        "top1_venue_share": 0.351,
        "price_dispersion_pct": 0.14,
        "coverage_state": "REPRESENTATIVE",
        "cex_volume_24h": 13941287000.0,
        "dex_volume_24h": 886062812.0,
        "pct_change_1h": -0.08,
        "pct_change_24h": 2.17,
        "pct_change_7d": 11.43,
        "market_cap_dominance": 11.37,
        "num_market_pairs_cmc": 8342,
        "circulating_supply": 120128917.0,
    },
}


def get_demo_report(symbol: str) -> dict | None:
    """Return a cached/demo report for a symbol, with timestamps filled in.

    Data transparency: every returned dict explicitly marks:
    - is_demo = True
    - data_mode = 'CACHED'
    - data_observation = 'CACHED SNAPSHOT — CMC API UNAVAILABLE'

    This data MUST NOT be presented as live market data.
    """
    data = DEMO_REPORTS.get(symbol.upper())
    if not data:
        return None
    import copy, datetime
    result = copy.deepcopy(data)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result["observation_timestamp"] = now
    result["is_demo"] = True
    result["data_mode"] = "CACHED"
    result["data_observation"] = "CACHED SNAPSHOT — CMC API UNAVAILABLE"
    if result.get("global_context"):
        result["global_context"]["last_updated"] = now
    for ev in result.get("evidence", []):
        ev["source_timestamp"] = now
    return result
