# Reality Gap

The **Reality Gap** measures the difference between an asset's aggregate "headline" metrics and the observable structural reality.

## How It Works

1. The engine fetches the "Headline" volume from the `/v2/cryptocurrency/quotes/latest` endpoint.
2. The engine fetches individual market pairs from `/v2/cryptocurrency/market-pairs/latest`.
3. The engine compares the headline volume against the sum of observable pair volumes.

## Metrics Calculated
- Headline vs Observed Volume divergence
- Top 5 Pair Concentration
- Top Venue Share
- Price Dispersion Percentage (Max - Min / Median)

## Important Limitations
- Headline volume calculations by CoinMarketCap may include proprietary weighting, exclusions, or venues not returned in the standard pairs list. A "Reality Gap" may simply indicate differences in aggregation methodology rather than wash trading.

## Relevant Source Files
- `apps/api/app/reality.py` (`detect_contradictions` and `calc_volume_concentration`)
