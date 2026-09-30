/**
 * MarketReality OS – API Client.
 *
 * Type-safe client for communicating with the FastAPI backend.
 * All CMC API calls go through the backend — the browser never touches CMC directly.
 */

import type {
  RealityReport,
  TradeRealityResult,
  StressScenario,
  StressResult,
  ApiStatus,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

class ApiClient {
  private base: string;

  constructor(base: string = API_BASE) {
    this.base = base;
  }

  private async fetch<T>(path: string, init?: RequestInit): Promise<T> {
    const url = `${this.base}${path}`;
    const res = await fetch(url, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });

    if (!res.ok) {
      let detail: string;
      try {
        const body = await res.json();
        detail = body.detail?.message || body.detail || JSON.stringify(body);
      } catch {
        detail = `HTTP ${res.status}: ${res.statusText}`;
      }
      throw new ApiError(detail, res.status);
    }

    return res.json();
  }

  /** Check backend connection and CMC config status. */
  async getStatus(): Promise<ApiStatus> {
    return this.fetch<ApiStatus>("/api/status");
  }

  /** Run a full Reality Audit for the given symbol. */
  async runRealityAudit(symbol: string): Promise<RealityReport> {
    return this.fetch<RealityReport>(`/api/reality/${encodeURIComponent(symbol)}`);
  }

  /** Assess structural tradability for a given trade. */
  async runTradeReality(
    symbol: string,
    tradeSizeUsd: number,
    side: "BUY" | "SELL"
  ): Promise<TradeRealityResult> {
    return this.fetch<TradeRealityResult>("/api/trade-reality", {
      method: "POST",
      body: JSON.stringify({
        symbol,
        trade_size_usd: tradeSizeUsd,
        side,
      }),
    });
  }

  /** List available stress scenarios. */
  async getStressScenarios(): Promise<{ scenarios: StressScenario[] }> {
    return this.fetch<{ scenarios: StressScenario[] }>("/api/stress/scenarios");
  }

  /** Run a stress scenario on an asset. */
  async runStressScenario(
    symbol: string,
    scenarioId: string
  ): Promise<StressResult> {
    return this.fetch<StressResult>(
      `/api/stress/${encodeURIComponent(symbol)}?scenario_id=${encodeURIComponent(scenarioId)}`
    , { method: "POST" });
  }

  /** Get all evidence objects for an asset. */
  async getEvidence(symbol: string): Promise<{
    asset: string;
    evidence_count: number;
    evidence: Array<Record<string, unknown>>;
    cmc_endpoints_used: string[];
  }> {
    return this.fetch(`/api/evidence/${encodeURIComponent(symbol)}`);
  }
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

/** Singleton API client instance. */
export const api = new ApiClient();
