# Trade Reality

Trade Reality provides a structural tradability assessment for a specific USD order size.

## Warning
**This is a structural assessment only — not an execution quote or slippage model.** MarketReality OS is not an execution engine.

## How It Works

The engine assesses the requested order size against the observed market structure across five dimensions:
1. **Market Coverage**: Total number of pairs observed.
2. **Volume Capacity**: Ratio of trade size to total 24h observed volume.
3. **Volume Concentration**: How much volume is locked in the top 5 pairs.
4. **Venue Dependence**: How much volume relies on the single largest venue.
5. **Price Agreement**: Level of price dispersion across venues.

## Outcomes
- **STRUCTURALLY_SUPPORTED**: Trade size is insignificant compared to deep, decentralized volume.
- **CONDITIONAL**: Trade is supported, but concentration or venue dependence poses routing risks.
- **CONSTRAINED**: Trade size is too large for the observed structural liquidity.
- **INSUFFICIENT_EVIDENCE**: Not enough CMC data available.

## Relevant Source Files
- `apps/api/app/reality.py` (`assess_tradability`)
