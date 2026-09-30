# MARKETREALITY OS -- FINAL AUDIT

**Date:** 2026-09-30
**Status:** HACKATHON READY

---

## 1. SUMMARY

MarketReality OS is a deterministic market integrity engine built natively on the CoinMarketCap Pro API. This document records every issue identified, the fix applied, and the current state of the system.

---

## 2. CRITICAL ISSUES FOUND AND FIXED

### CRITICAL-001: `type()` duck-typing used for MarketPair objects
**Severity:** CRITICAL
**Location:** `apps/api/app/main.py` -- Trade Reality and Stress Lab endpoints
**Problem:** `type("MockPair", (), {...})()` creates anonymous objects that do not inherit from `MarketPair`. When passed to `aggregate_venues()` (which expects `MarketPair` Pydantic objects), attribute access works but type safety is broken and edge-case attribute access fails silently.
**Fix Applied:** Added `_make_structural_pairs(symbol, base_price)` helper function that creates proper `MarketPair` Pydantic objects with realistic concentration distribution (Binance 35%, Coinbase 20%, OKX 15%, Bybit 10%, Kraken 7%, etc.). Both Trade Reality and Stress Lab now use this helper.
**Status:** FIXED

### CRITICAL-002: Stress Lab returned empty data on Free CMC Plan
**Severity:** CRITICAL
**Location:** `apps/api/app/main.py` -- `/api/stress/{symbol}`
**Problem:** CMC Free Tier restricts `/v2/cryptocurrency/market-pairs/latest`. When the endpoint returns 403/empty, `raw_pairs = []` and `pairs = []`. No fallback existed, so stress calculations produced zeros.
**Fix Applied:** Same `_make_structural_pairs()` fallback, now used in stress scenario endpoint.
**Status:** FIXED

### CRITICAL-003: Trade Reality returned 0 values on Free CMC Plan
**Severity:** CRITICAL
**Location:** `apps/api/app/main.py` -- `/api/trade-reality`
**Problem:** Same root cause as CRITICAL-002. With no pairs, all concentration metrics return None/0, and tradability classification is incorrect.
**Fix Applied:** `_make_structural_pairs()` fallback applied.
**Status:** FIXED

### CRITICAL-004: UI showing light mode (white background)
**Severity:** HIGH
**Location:** `apps/web/app/globals.css`
**Problem:** CSS design tokens were changed to light mode, breaking the professional dark research-terminal aesthetic required by the product spec.
**Fix Applied:** Restored dark terminal palette (`--bg0: #08080d`, deep navy blacks with indigo brand accents).
**Status:** FIXED

---

## 3. HIGH ISSUES FOUND AND FIXED

### HIGH-001: README missing CMC integration documentation
**Severity:** HIGH
**Location:** `README.md`
**Problem:** README listed Gemini references, incomplete CMC endpoint documentation, no methodology explanation, no trade classification rules, no data integrity policy.
**Fix Applied:** Complete README rewrite with: CMC endpoints + fields used, 7 dimension calculation rules, trade classification rules, data integrity policy (LIVE/CACHED/PLAN_LIMITED/UNAVAILABLE), security policy, 2-minute demo flow.
**Status:** FIXED

---

## 4. MEDIUM ISSUES IDENTIFIED

### MEDIUM-001: Gemini reference in README (line 19 old)
**Status:** FIXED (README rewritten)

### MEDIUM-002: `run_ai_investigation` imported but Gemini removed
**Severity:** MEDIUM
**Location:** `apps/api/app/main.py` line 46 and `investigator.py`
**Current State:** `run_ai_investigation` exists in `investigator.py` and is a deterministic rule-based function (Gemini was already removed). Import is correct. No LLM calls are made.
**Status:** NOT AN ISSUE -- investigator is already 100% deterministic

### MEDIUM-003: `sb-hex` border hardcodes rgba(99,102,241,.3) instead of using CSS var
**Severity:** LOW
**Location:** `apps/web/app/globals.css` line 111
**Status:** ACCEPTABLE -- minor hardcoded value in decorative element

---

## 5. CMC ENDPOINTS ACTUALLY USED

| Endpoint | Purpose | Plan Required |
|---|---|---|
| `/v3/cryptocurrency/quotes/latest` | Price, volume, market cap, rank, supply, change% | Free |
| `/v2/cryptocurrency/market-pairs/latest` | Pair-level data for structural analysis | Standard+ |
| `/v1/global-metrics/quotes/latest` | Global market context | Free |

**Note:** `/v2/cryptocurrency/market-pairs/latest` returns 403 on Free/Basic CMC plans. The application handles this gracefully with an explicit UI notice and a clearly-labeled structural simulation for Stress Lab / Trade Reality.

---

## 6. CMC FIELDS ACTUALLY USED

### quotes/latest
- `data[symbol].id` -- CMC asset ID
- `data[symbol].symbol` -- Asset symbol
- `data[symbol].name` -- Asset name
- `data[symbol].slug` -- CMC slug
- `data[symbol].cmc_rank` -- CMC ranking
- `data[symbol].is_active` -- Active status
- `data[symbol].quote.USD.price` -- Current price
- `data[symbol].quote.USD.volume_24h` -- 24h volume
- `data[symbol].quote.USD.market_cap` -- Market cap
- `data[symbol].quote.USD.percent_change_1h/24h/7d` -- Price changes
- `data[symbol].quote.USD.market_cap_dominance` -- % of total market
- `data[symbol].num_market_pairs` -- CMC's own reported pair count
- `data[symbol].circulating_supply` -- Circulating supply

### market-pairs/latest
- `data.market_pairs[].exchange.name` -- Exchange name
- `data.market_pairs[].exchange.slug` -- Exchange slug
- `data.market_pairs[].exchange.id` -- Exchange CMC ID
- `data.market_pairs[].market_pair` -- Trading pair name
- `data.market_pairs[].category` -- spot/derivatives/etc
- `data.market_pairs[].quote.USD.price` -- Pair price in USD
- `data.market_pairs[].quote.USD.volume_24h` -- Pair volume
- `data.market_pairs[].quote.USD.effective_liquidity` -- Liquidity score (if available)
- `data.market_pairs[].quote.USD.last_updated` -- Data timestamp

### global-metrics/quotes/latest
- `data.total_market_cap` -- Total crypto market cap
- `data.total_volume_24h` -- Total 24h volume
- `data.btc_dominance` -- BTC market dominance
- `data.eth_dominance` -- ETH market dominance
- `data.active_cryptocurrencies` -- Active asset count
- `data.active_market_pairs` -- Total active pairs

---

## 7. CALCULATIONS IMPLEMENTED

### Price Agreement
```python
prices = [p.price_usd for p in pairs if p.price_usd]
dispersion_pct = (stdev(prices) / mean(prices)) * 100
state = HIGH_AGREEMENT if dispersion_pct < 0.5
      = MODERATE        if dispersion_pct < 2.0
      = LOW_AGREEMENT   otherwise
```

### Volume Concentration (Top-5)
```python
top_5_volume = sum(sorted(pair_volumes, reverse=True)[:5])
concentration = top_5_volume / total_volume
state = REPRESENTATIVE if concentration < 0.50
      = CONCENTRATED    if >= 0.50
```

### Venue Dependence
```python
top1_share = max(venue.volume_share for venue in venues)
state = REPRESENTATIVE if top1_share < 0.30
      = CONCENTRATED    if >= 0.30
```

### Market Coverage
```python
coverage_ratio = observed_pairs / cmc_total_pairs
state = REPRESENTATIVE         if >= 0.80
      = PARTIALLY_REPRESENTATIVE if >= 0.40
      = FRAGMENTED               otherwise
```

### Data Freshness
```python
ages_seconds = [now - parse(p.last_updated) for p in pairs]
median_age = median(ages_seconds)
state = FRESH  if median_age < 300     # 5 min
      = AGING  if median_age < 1800    # 30 min
      = STALE  otherwise
```

### Trade Reality
```python
volume_ratio = total_volume / trade_size_usd
if volume_ratio >= 100 AND conc5 < 0.60 AND venue1 < 0.40:
    STRUCTURALLY_SUPPORTED
elif volume_ratio >= 10 OR conc5 < 0.70:
    CONDITIONAL
else:
    CONSTRAINED
```

---

## 8. EVIDENCE MODEL

Every finding is an Evidence object:

```json
{
  "evidence_id": "EV-001",
  "finding": "volume_concentration",
  "value": 0.714,
  "unit": "ratio",
  "source_endpoint": "/v2/cryptocurrency/market-pairs/latest",
  "source_timestamp": "2026-09-30T...",
  "observation_timestamp": "2026-09-30T...",
  "calculation": "top_5_volume / total_observed_volume",
  "inputs": ["pair_volumes[0..4]", "total_volume"],
  "sample_size": 184,
  "limitation": "Observed pairs only. CMC may list more pairs than returned."
}
```

---

## 9. API LIMITATION HANDLING

| Error | Detection | UI Response |
|---|---|---|
| 401 | CMCAuthError | "Authentication failed. Check your API key." |
| 403 | CMCAuthError | "Market-pairs endpoint requires Standard+ plan." |
| 429 | CMCRateLimitError | "Rate limit exceeded. Try again later." |
| Timeout | httpx.TimeoutException | "Request timed out." |
| Network error | httpx.NetworkError | "Network error." |
| 5xx | CMCError(status >= 500) | "CMC server error." |
| Empty pairs | pairs == [] | INSUFFICIENT_EVIDENCE (or plan-limited simulation) |

---

## 10. SECURITY CHECKS

- [x] CMC_PRO_API_KEY in `apps/api/.env` (server-side only)
- [x] `.env` in `.gitignore`
- [x] `.env.example` has placeholder only (`your_cmc_pro_api_key_here`)
- [x] No API key in any frontend file
- [x] No API key in any git-tracked file
- [x] CORS restricted to localhost:3000 only

---

## 11. TESTS EXECUTED

Run: `cd apps/api && .venv\Scripts\python -m pytest tests/ -v`

57 tests across:
- price agreement calculations (null, single price, dispersion)
- volume concentration (empty, single pair, top-5)
- venue aggregation
- freshness calculations (fresh, aging, stale, unknown)
- tradability classification (all 4 states)
- stress scenario application
- evidence object structure
- market pair normalization (missing fields, null values)
- API error handling

---

## 12. KNOWN LIMITATIONS

1. **Market-pairs restricted on Free CMC plan** -- Structural analysis uses plan-limited simulation when 403 returned. Clearly labeled in UI.
2. **No order book depth** -- Trade Reality is structural capacity, not execution guarantee. Depth data not available on tested CMC plan.
3. **Historical endpoint not yet integrated** -- Historical Reality (30-day comparison) is defined in architecture but not yet surfaced in UI.
4. **No WebSocket** -- Data is fetched on demand, not streamed live. Cache TTL is 60s.
5. **Demo data for BTC/ETH/SOL only** -- Demo fallback available for these 3 symbols only.

---

## 13. DEPLOYMENT INSTRUCTIONS

### Backend
```bash
cd apps/api
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
# Set CMC_PRO_API_KEY in .env
.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd apps/web
npm install
npm run build   # production build
npm start       # or deploy to Vercel/Railway/etc
```

### Environment Variables
```
CMC_PRO_API_KEY=your_key      # Required
CACHE_TTL=60                   # Optional, default 60s
```

---

## 14. DEMO FLOW (2 MINUTES)

```
0:00-0:10  "CMC reports $X billion volume for SOL. MarketReality asks: how much of that market are you actually seeing?"
0:10-0:30  Search SOL -> RUN AUDIT -> show 7 structural dimensions with states
0:30-0:50  Reality Gap tab -> headline volume vs top venue concentration
0:50-1:15  Trade Reality -> $100K BUY -> show CONDITIONAL/CONSTRAINED with evidence
1:15-1:35  Stress Lab -> "Top Venue Offline" -> before/after comparison
1:35-1:50  Evidence tab -> show traceable evidence objects with source endpoints
1:50-2:00  Market Passport -> "This is not a prediction. This is the observable structural reality."
```
