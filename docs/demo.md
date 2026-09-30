# MarketReality OS Demo Guide

MarketReality OS includes a fallback Demo/Mock system to ensure evaluators can experience the UI even if they do not have a CoinMarketCap API key.

## Data State System

The system operates in one of three data modes (`apps/api/app/models.py` -> `DataMode`):

1. **LIVE**: Fetches fresh data directly from the CMC API.
2. **CACHED**: If rate limited or plan-restricted, falls back to a previous valid snapshot.
3. **UNAVAILABLE**: Endpoint inaccessible and no cache exists.

*(Note: "DEVELOPMENT SAMPLE" or "DEMO DATA" is explicitly flagged in the UI when the `DEMO_MODE=true` flag is set or the API key is missing.)*

## How to Trigger the Demo

1. Ensure `.env` has `DEMO_MODE=true` (or do not provide a `CMC_PRO_API_KEY`).
2. Search for any standard asset (BTC, SOL).
3. The UI will explicitly display **"⬡ DEMO DATA"** tags to ensure it is never silently presented as live market data.

## Relevant Source Files
- `apps/api/app/demo.py`
- `apps/api/app/main.py`
