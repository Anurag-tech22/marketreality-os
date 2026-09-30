# CMC Integration & API Evidence

MarketReality OS is built directly on the CoinMarketCap (CMC) API. This document details the exact endpoints used, capabilities enabled, and limitations encountered.

## What CMC Made Possible
- **Global Breadth**: Access to thousands of market pairs across hundreds of exchanges via a single unified interface.
- **Instant Normalization**: CMC standardizes volume and price into USD, eliminating the need to run cross-currency conversions.
- **Identity Resolution**: `cmc_id` allows us to unambiguously identify assets, avoiding ticker collisions (e.g., distinguishing between different assets using the symbol "MEME").

## Where CMC Got in the Way (Actual Limitations)
- **Plan Restrictions**: Many rich endpoints (e.g., order book depth, historical quotes) require high-tier enterprise plans.
- **Market Pairs Limit**: The free tier restricts `/v2/cryptocurrency/market-pairs/latest` to a maximum number of results, preventing deep-tail analysis of heavily fragmented assets.
- **Endpoint Availability**: When rate limits are hit or plan limits exceeded, the engine is forced to fallback to cached snapshots.

## API Evidence: Endpoints Used

### 1. Asset Mapping
- **Endpoint**: `/v1/cryptocurrency/map`
- **Purpose**: Resolves user-provided symbols to internal `cmc_id`.

### 2. Latest Quotes
- **Endpoint**: `/v2/cryptocurrency/quotes/latest`
- **Purpose**: Fetches the "headline" metrics (price, market cap, circulating supply).

### 3. Market Pairs
- **Endpoint**: `/v2/cryptocurrency/market-pairs/latest`
- **Purpose**: Fetches the actual venue-level exchange pairs used for structural analysis.

## Actual Request Code

From `apps/api/app/services/cmc/client.py`:

```python
self._client = httpx.AsyncClient(
    base_url=settings.cmc_base_url,
    timeout=httpx.Timeout(8.0, connect=5.0),
    headers={
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-CMC_PRO_API_KEY": settings.cmc_pro_api_key,
    },
)
```

## Relevant Source Files
- `apps/api/app/services/cmc/client.py`
- `apps/api/app/services/cmc/market_pairs.py`
