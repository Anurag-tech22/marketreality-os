# Methodology

## Core Principle

> AI is NOT the calculator. Python deterministic code calculates facts. AI explains, investigates, challenges, and summarizes those facts.

## Market Reality Dimensions

MarketReality uses independent descriptive dimensions rather than an arbitrary 0–100 score:

### Price Agreement
- **Calculation**: `(max_price - min_price) / median_price × 100` across all observed market pairs
- **States**:
  - `HIGH_AGREEMENT`: Dispersion < 0.5%
  - `MODERATE_AGREEMENT`: Dispersion 0.5% – 2.0%
  - `LOW_AGREEMENT`: Dispersion 2.0% – 5.0%
  - `INCONSISTENT`: Dispersion > 5.0%
  - `SINGLE_SOURCE`: Only one price observed
  - `INSUFFICIENT_EVIDENCE`: No prices observed
- **Limitation**: Prices from CMC-returned pairs only

### Volume Concentration
- **Calculation**: `sum(top_N_pair_volumes) / sum(all_pair_volumes)`
- **Reported at**: Top-1, Top-5, Top-10 levels
- **States**:
  - `REPRESENTATIVE`: Top-5 < 50%
  - `PARTIALLY_REPRESENTATIVE`: Top-5 50% – 70%
  - `CONCENTRATED`: Top-5 ≥ 70%
  - `INSUFFICIENT_EVIDENCE`: No volume data
- **Limitation**: Concentration over returned pairs (max 500)

### Venue Dependence
- **Calculation**: Exchange volumes aggregated from individual pair volumes
- **Metric**: Top-1 venue's share of total observed volume
- **States**:
  - `REPRESENTATIVE`: Top venue < 25%
  - `PARTIALLY_REPRESENTATIVE`: Top venue 25% – 50%
  - `CONCENTRATED`: Top venue ≥ 50%
- **Limitation**: Venues derived from CMC-returned pairs

### Market Coverage
- **Metric**: Count of observed pairs and unique venues
- **States**:
  - `HIGH`: ≥ 100 pairs AND ≥ 20 venues
  - `MODERATE`: ≥ 30 pairs AND ≥ 10 venues
  - `LOW`: ≥ 5 pairs
  - `MINIMAL`: < 5 pairs
  - `INSUFFICIENT_EVIDENCE`: No pairs
- **Limitation**: Limited to CMC API response (max 500 pairs)

### Data Freshness
- **Calculation**: Median age of `last_updated` timestamps from market pairs
- **States**:
  - `FRESH`: Median age < 5 minutes
  - `AGING`: Median age 5 min – 1 hour
  - `STALE`: Median age > 1 hour
  - `UNKNOWN`: No timestamps available

### Cross-Market Consistency
- **Analysis**: Automated detection of structural contradictions
- **Detected patterns**:
  - High volume with low market coverage
  - High concentration despite broad venue count
  - Large price divergence
  - Stale data
  - Observed volume significantly below headline volume

### Evidence Completeness
- **Assessment dimensions**: Coverage, freshness, venue breadth, price samples, contradictions
- **States**:
  - `SUFFICIENT`: Score ≥ 5 (strong coverage, fresh data, broad venues)
  - `LIMITED`: Score 2–4
  - `INSUFFICIENT`: Score < 2

## Reality Gap

The Reality Gap shows the difference between:
- **Headline Market**: CMC-reported aggregate price, volume, market cap
- **Observed Structure**: What the pair-level data actually reveals

This is not a claim that the headline number is "wrong." It shows how its composition affects interpretation.

## Trade Reality (Structural Tradability)

Trade Reality is a **structural assessment**, not an execution quote.

- **Input**: Asset, trade size (USD), side (BUY/SELL)
- **Assessed dimensions**: Market coverage, volume capacity, volume concentration, venue dependence, price agreement, freshness
- **States**:
  - `STRUCTURALLY_SUPPORTED`: All dimensions favorable
  - `CONDITIONAL`: Some concerning dimensions
  - `CONSTRAINED`: Multiple concerning dimensions or insufficient evidence
  - `INSUFFICIENT_EVIDENCE`: Not enough data

**Important**: This does NOT predict execution slippage, order book impact, or actual fill prices.

## Stress Lab

Stress scenarios are **structural simulations**, not predictions.

- Remove top venue → recalculate all metrics
- Remove top 5 pairs → recalculate
- Increase concentration → boost top pair volumes
- Reduce coverage → remove bottom pairs
- Price shock → apply percentage change
- Multiply price dispersion → widen spread from median

## Evidence Quality

Evidence quality is assessed across independent sub-dimensions, NOT as a single AI confidence score:

- Coverage (pair and venue count)
- Freshness (timestamp age)
- Consistency (contradiction presence)
- Sample Size (price observation count)

**Core rule: NO EVIDENCE → NO CLAIM.**
