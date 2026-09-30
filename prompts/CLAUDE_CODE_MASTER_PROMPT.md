# Claude Code Master Prompt — MARKETREALITY OS

You are taking over the MarketReality OS repository.

Your job is to turn this starter into a serious hackathon submission for the CoinMarketCap API Hackathon.

## Product

MARKETREALITY OS is a market integrity and tradability intelligence engine.

Core promise:

"Before an AI agent or human acts on a market, verify what the market actually looks like."

Do NOT turn this into a generic crypto dashboard, generic AI analyst, generic chatbot, generic portfolio tracker, generic MCP wrapper, or buy/sell signal generator.

## Non-negotiable principles

1. Real CMC data only for live claims.
2. No fabricated fallback market numbers.
3. Deterministic calculations are the source of truth.
4. AI explains, challenges, and synthesizes evidence; it does not invent numbers.
5. Every material finding has provenance.
6. Missing data must become an explicit unavailable/insufficient state.
7. API keys stay server-side.
8. Do not expose CMC keys in browser bundles.
9. Do not commit secrets.
10. Preserve working code instead of rewriting it unnecessarily.

## Core product modules

- Reality Audit
- Evidence Graph
- Trade Reality
- Stress Lab
- Historical Reality
- CEX ↔ DEX Reality
- Derivatives Reality
- CMC AI context
- CMC MCP agent layer
- AI Investigator
- AI Red Team
- Market Passport

## CMC integration

Implement incrementally and verify every endpoint against current CMC documentation.

Priority:

1. cryptocurrency map
2. cryptocurrency quotes/latest
3. cryptocurrency market-pairs/latest
4. historical quotes/OHLCV
5. exchange market-pairs
6. global metrics
7. CMC AI
8. DEX where supported
9. derivatives where supported
10. RWA where useful

Do not use endpoint count as a metric.

## Reality Engine

Implement deterministic calculations for:

- observed pair count
- total observed pair volume
- top-1 volume concentration
- top-5 volume concentration
- venue concentration
- price dispersion
- market coverage
- freshness
- cross-market agreement
- evidence completeness

Return descriptive states rather than an opaque 0-100 score.

## Evidence model

Every finding must contain:

- id
- finding
- value
- unit
- source endpoint
- timestamp
- calculation
- sample size
- limitation

## Trade Reality

Input:

- asset
- trade size
- buy/sell

Output a structural assessment.

Never claim exact execution slippage unless the data supports it.

## Stress Lab

Support deterministic scenario transforms:

- remove dominant venue
- reduce market coverage
- increase volume concentration
- increase price dispersion
- market shock
- custom scenario

Clearly label simulations as simulations.

## AI Investigator

Input only normalized evidence.

Require:

- evidence IDs
- observation vs interpretation separation
- explicit limitations
- no invented values

## AI Red Team

For every conclusion, generate:

- possible alternative explanation
- missing evidence
- data coverage limitations
- what additional observation would strengthen or weaken the finding

## CMC MCP

CMC's official MCP endpoint is:

https://mcp.coinmarketcap.com/mcp

Use header:

X-CMC-MCP-API-KEY

CMC MCP is a data access layer. MarketReality itself should provide the investigation tools on top.

Do not simply clone CMC's existing MCP tools.

Create higher-level MarketReality tools such as:

- market_reality_check
- market_structure_audit
- trade_reality_check
- stress_market
- get_evidence
- challenge_finding
- generate_market_passport

## UI

Make the interface feel like a serious research terminal:

- dark
- restrained
- dense but readable
- evidence-first
- excellent typography
- clear hierarchy
- subtle motion
- no neon crypto cliché
- no giant decorative charts without meaning

The strongest demo path is:

1. Search SOL/BTC/ETH
2. Run Reality Audit
3. Open Evidence Graph
4. Enter $100K Trade Reality
5. Break the dominant venue
6. Show before/after structural evidence
7. Run AI Red Team
8. Generate Market Passport

## Engineering

Before declaring anything complete:

- run typecheck
- run tests
- run backend tests
- test missing API key
- test malformed CMC response
- test null values
- test zero volumes
- test duplicate pairs
- test stale data
- test empty responses
- test rate-limit/error handling

Do not hide errors.

## Deliverable

The result should look and behave like a real product, not an AI-generated mockup.
