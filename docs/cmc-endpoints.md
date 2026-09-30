# CMC API Endpoints

> All endpoints are called server-side only. API keys never reach the browser.

## Endpoints Used

| Endpoint | Version | Purpose | Feature |
|----------|---------|---------|---------|
| `/v1/cryptocurrency/map` | v1 | Resolve symbol → CMC ID, name, slug, rank | Identity resolution |
| `/v2/cryptocurrency/quotes/latest` | v2 | Current price, volume, market cap | Reality Audit headline metrics |
| `/v2/cryptocurrency/market-pairs/latest` | v2 | Market pair discovery (up to 500 pairs per request) | Volume concentration, venue dependence, price agreement, coverage, freshness |
| `/v1/global-metrics/quotes/latest` | v1 | Global market cap, volume, BTC/ETH dominance | Global context layer |
| `/v3/cryptocurrency/quotes/historical` | v3 | Historical quotes for time comparison | Historical Reality (Phase 6) |
| `/v2/cryptocurrency/ohlcv/historical` | v2 | Historical OHLCV candles | Historical Reality (Phase 6) |
| `/v1/exchange/market-pairs/latest` | v1 | Exchange-level market pairs | Exchange analysis (Phase 7) |

## MCP

Official CMC MCP endpoint:

`https://mcp.coinmarketcap.com/mcp`

Header: `X-CMC-MCP-API-KEY`

## What Each Endpoint Enables

### `/v1/cryptocurrency/map`
- Stable CMC ID resolution (avoids symbol ambiguity)
- Asset name, slug, rank, active status
- Foundation for all subsequent lookups

### `/v2/cryptocurrency/quotes/latest`
- Headline price, 24h volume, market cap
- Forms the "headline market" side of the Reality Gap
- Provides the benchmark that structural analysis compares against

### `/v2/cryptocurrency/market-pairs/latest`
- **Core structural data source** — most calculations derive from this endpoint
- Volume concentration (top-1, top-5, top-10)
- Venue dependence (exchange-level aggregation)
- Price agreement (cross-market price dispersion)
- Market coverage (pair count, venue count)
- Data freshness (timestamp age analysis)
- Contradiction detection (structural pattern analysis)

### `/v1/global-metrics/quotes/latest`
- Global market cap, volume, BTC/ETH dominance
- Active cryptocurrencies, exchanges, market pairs
- Contextual framing for individual asset analysis

## Limitations

- Market pairs endpoint returns max 500 pairs per request
- Some exchanges may not report to CMC
- Volume methodologies vary across exchanges
- DEX data coverage depends on CMC's on-chain indexing
- API rate limits apply (plan-dependent)
- Historical data availability depends on CMC plan tier

## Important

Verify all endpoint paths and parameters against current CMC documentation before implementation. API versions and availability can change.
