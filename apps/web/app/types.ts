/**
 * MarketReality OS – TypeScript type definitions.
 *
 * These types mirror the backend Pydantic models to ensure type safety
 * across the full stack.
 */

// ── Enums ──────────────────────────────────────────────────────

export type RealityState =
  | "REPRESENTATIVE"
  | "PARTIALLY_REPRESENTATIVE"
  | "FRAGMENTED"
  | "CONCENTRATED"
  | "INCONSISTENT"
  | "INSUFFICIENT_EVIDENCE";

export type DataMode = "LIVE" | "CACHED" | "UNAVAILABLE";

export type TradabilityState =
  | "STRUCTURALLY_SUPPORTED"
  | "CONDITIONAL"
  | "CONSTRAINED"
  | "INSUFFICIENT_EVIDENCE";

export type EvidenceQuality = "SUFFICIENT" | "LIMITED" | "INSUFFICIENT";

export type FreshnessState = "FRESH" | "AGING" | "STALE" | "UNKNOWN";

export type MarketType = "CEX" | "DEX" | "UNKNOWN";

// ── Evidence ───────────────────────────────────────────────────

export interface Evidence {
  evidence_id: string;
  finding: string;
  value: number | string | null;
  unit?: string | null;
  source_endpoint: string;
  source_timestamp?: string | null;
  observation_timestamp: string;
  calculation: string;
  inputs?: string[];
  sample_size?: number | null;
  limitation?: string | null;
}

// ── Asset ──────────────────────────────────────────────────────

export interface Asset {
  symbol: string;
  name?: string | null;
  slug?: string | null;
  cmc_id?: number | null;
  cmc_rank?: number | null;
  is_active: boolean;
}

// ── Market pair ────────────────────────────────────────────────

export interface MarketPair {
  exchange_name: string;
  exchange_slug?: string | null;
  exchange_id?: number | null;
  market_pair: string;
  market_type: MarketType;
  category?: string | null;
  base_symbol?: string | null;
  quote_symbol?: string | null;
  price_usd?: number | null;
  volume_24h_usd?: number | null;
  volume_percent?: number | null;
  effective_liquidity?: number | null;
  last_updated?: string | null;
}

// ── Venue ──────────────────────────────────────────────────────

export interface Venue {
  name: string;
  slug?: string | null;
  exchange_id?: number | null;
  market_type: MarketType;
  total_volume_24h_usd: number;
  pair_count: number;
  volume_share: number;
}

// ── Global context ─────────────────────────────────────────────

export interface GlobalMarketContext {
  total_market_cap_usd?: number | null;
  total_volume_24h_usd?: number | null;
  btc_dominance?: number | null;
  eth_dominance?: number | null;
  active_cryptocurrencies?: number | null;
  active_exchanges?: number | null;
  total_market_pairs?: number | null;
  last_updated?: string | null;
  source_endpoint: string;
}

// ── Reality dimension ──────────────────────────────────────────

export interface RealityDimension {
  name: string;
  state: string;
  value?: number | null;
  display_value?: string | null;
  evidence_ids: string[];
  description?: string | null;
}

// ── Reality Gap ────────────────────────────────────────────────

export interface RealityGap {
  headline_volume_24h?: number | null;
  headline_market_cap?: number | null;
  headline_price?: number | null;
  observed_pair_count: number;
  observed_total_volume?: number | null;
  top5_concentration?: number | null;
  top1_venue_share?: number | null;
  price_dispersion_pct?: number | null;
  coverage_state: string;
  // Enriched fields from CMC quotes endpoint
  cex_volume_24h?: number | null;
  dex_volume_24h?: number | null;
  pct_change_1h?: number | null;
  pct_change_24h?: number | null;
  pct_change_7d?: number | null;
  market_cap_dominance?: number | null;
  num_market_pairs_cmc?: number | null;
  circulating_supply?: number | null;
}

// ── Reality Report ─────────────────────────────────────────────

export interface RealityReport {
  asset: string;
  asset_info?: Asset | null;
  status: string;
  observation_timestamp: string;
  dimensions: RealityDimension[];
  reality_gap?: RealityGap | null;
  venues: Venue[];
  market_pairs_sample: MarketPair[];
  evidence: Evidence[];
  global_context?: GlobalMarketContext | null;
  limitations: string[];
  cmc_endpoints_used: string[];
  // Data transparency fields — always present in API response
  is_demo: boolean;
  data_mode: DataMode;
  data_observation: string;
}

// ── Trade Reality ──────────────────────────────────────────────

export interface TradeRealityRequest {
  symbol: string;
  trade_size_usd: number;
  side: "BUY" | "SELL";
}

export interface TradeRealityDimension {
  name: string;
  state: string;
  value?: number | null;
  display_value?: string | null;
  evidence_ids?: string[];
}

export interface TradeRealityResult {
  asset: string;
  trade_size_usd: number;
  side: string;
  result: TradabilityState;
  dimensions: TradeRealityDimension[];
  evidence: Evidence[];
  limitations: string[];
  observation_timestamp: string;
}

// ── Stress Lab ─────────────────────────────────────────────────

export interface StressScenario {
  id: string;
  name: string;
  description: string;
  parameter?: string | null;
  value?: number | null;
}

export interface StressResult {
  scenario: StressScenario;
  before: Record<string, number | string | null>;
  after: Record<string, number | string | null>;
  affected_dimensions: string[];
  evidence: Evidence[];
  observation_timestamp: string;
}

// ── API Status ─────────────────────────────────────────────────

export interface ApiStatus {
  cmc_configured: boolean;
  cmc_mcp_configured: boolean;
  gemini_configured: boolean;
}

// ── API Error ──────────────────────────────────────────────────

export interface ApiError {
  error: string;
  message: string;
  endpoint?: string;
}
