# Stress Lab

The Stress Lab allows users to simulate structural shocks to the market and observe how the Reality Dimensions change.

## How It Works

The engine clones the current observed market pairs and venues, applies a mathematical transformation, and re-runs the entire reality calculation pipeline.

## Scenarios
- **Top Venue Unavailable**: Removes all pairs belonging to the #1 exchange.
- **Market Coverage -30%**: Removes the bottom 30% of pairs by volume.
- **Price Dispersion x2**: Artificially widens the spread from the median price.
- **-20% Market Shock**: Adjusts all pair prices downward by 20%.

## Important Limitations
- Stress tests are purely hypothetical structural simulations. They do not simulate order book depth clearing or cascading liquidations.

## Relevant Source Files
- `apps/api/app/reality.py` (`apply_stress_scenario`)
