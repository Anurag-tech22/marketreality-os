"use client";

import { useState, useEffect, useCallback, useRef } from "react";

// ── Types ──────────────────────────────────────────────────────────────────────
interface Asset { symbol: string; name?: string; slug?: string; cmc_id?: number; cmc_rank?: number; is_active?: boolean; }
interface RealityGap {
  headline_price?: number; headline_volume_24h?: number; headline_market_cap?: number;
  observed_pair_count: number; observed_total_volume?: number;
  top5_concentration?: number; top1_venue_share?: number;
  price_dispersion_pct?: number; coverage_state: string;
  cex_volume_24h?: number; dex_volume_24h?: number;
  pct_change_1h?: number; pct_change_24h?: number; pct_change_7d?: number;
  market_cap_dominance?: number; num_market_pairs_cmc?: number; circulating_supply?: number;
}
interface Dimension { name: string; state: string; value?: number; display_value?: string; description?: string; evidence_ids: string[]; }
interface Venue { name: string; total_volume_24h_usd: number; pair_count: number; volume_share: number; market_type: string; }
interface Evidence { evidence_id: string; finding: string; value: any; unit?: string; source_endpoint: string; calculation: string; limitation?: string; sample_size?: number; source_timestamp?: string; }
interface GlobalCtx { total_market_cap_usd?: number; total_volume_24h_usd?: number; btc_dominance?: number; eth_dominance?: number; active_cryptocurrencies?: number; active_exchanges?: number; last_updated?: string; }
interface StressScenario { id: string; name: string; description: string; }
interface StressResult { scenario: StressScenario; before: Record<string, any>; after: Record<string, any>; affected_dimensions: string[]; }
interface TradeResult { result: string; dimensions: { name: string; state: string; display_value?: string }[]; limitations: string[]; }
interface InvestigationResult { verdict: string | null; model: string | null; grounded: boolean; error: string | null; is_demo?: boolean; }
interface Report {
  asset: string; asset_info?: Asset; status: string; observation_timestamp: string;
  dimensions: Dimension[]; reality_gap?: RealityGap;
  venues: Venue[]; evidence: Evidence[]; global_context?: GlobalCtx;
  limitations: string[]; cmc_endpoints_used: string[];
  is_demo: boolean; data_mode: string; data_observation: string;
}

// ── API ────────────────────────────────────────────────────────────────────────
const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function apiFetch(path: string, opts?: RequestInit, timeoutMs = 25000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const r = await fetch(`${API}${path}`, { ...opts, signal: controller.signal });
    clearTimeout(timer);
    if (!r.ok) {
      const e = await r.json().catch(() => ({}));
      throw new Error(e?.detail?.message || e?.detail || `HTTP ${r.status}`);
    }
    return r.json();
  } catch (e: any) {
    clearTimeout(timer);
    if (e.name === "AbortError") throw new Error("Request timed out. Serving cached data…");
    throw e;
  }
}

const fetchReport = (sym: string, demo = false): Promise<Report> =>
  apiFetch(demo ? `/api/demo/${sym}` : `/api/reality/${sym}`);

const fetchScenarios = () =>
  apiFetch("/api/stress/scenarios", undefined, 8000).then(d => d.scenarios ?? []);

const fetchInvestigation = (sym: string, demo = false): Promise<InvestigationResult> =>
  apiFetch(demo ? `/api/investigate/demo/${sym}` : `/api/investigate/${sym}`, undefined, 30000);

async function runStress(sym: string, sid: string): Promise<StressResult> {
  return apiFetch(`/api/stress/${sym}?scenario_id=${sid}`, { method: "POST" });
}

async function runTrade(sym: string, size: number, side: string): Promise<TradeResult> {
  return apiFetch("/api/trade-reality", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol: sym, trade_size_usd: size, side }),
  });
}

// ── Formatters ─────────────────────────────────────────────────────────────────
const f = {
  price: (n?: number | null) => n == null ? "—"
    : n >= 1000 ? `$${n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : n >= 1    ? `$${n.toFixed(4)}`
    : `$${n.toFixed(6)}`,
  usd: (n?: number | null) => n == null ? "—"
    : n >= 1e12 ? `$${(n/1e12).toFixed(2)}T`
    : n >= 1e9  ? `$${(n/1e9).toFixed(2)}B`
    : n >= 1e6  ? `$${(n/1e6).toFixed(1)}M`
    : n >= 1e3  ? `$${(n/1e3).toFixed(1)}K`
    : `$${n.toFixed(2)}`,
  pct: (n?: number | null) => n == null ? "—" : `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`,
  ratio: (n?: number | null) => n == null ? "—" : `${(n * 100).toFixed(1)}%`,
  num: (n?: number | null) => n == null ? "—" : n.toLocaleString(),
  ts: (s?: string | null) => { try { return s ? new Date(s).toLocaleTimeString() : "—"; } catch { return "—"; } },
};

// ── State color system ─────────────────────────────────────────────────────────
const STATE_COLOR: Record<string, string> = {
  REPRESENTATIVE: "green", EVIDENCE_READY: "green", STRUCTURALLY_SUPPORTED: "green",
  HIGH_AGREEMENT: "green", FRESH: "green", SUFFICIENT: "green",
  PARTIALLY_REPRESENTATIVE: "amber", CONDITIONAL: "amber", LIMITED_EVIDENCE: "amber",
  MODERATE_AGREEMENT: "amber", AGING: "amber", LIMITED: "amber",
  CONCENTRATED: "red", CONSTRAINED: "red", FRAGMENTED: "red", INCONSISTENT: "red",
  LOW_AGREEMENT: "red", STALE: "red", INSUFFICIENT: "red",
  QUOTE_ONLY: "blue", SINGLE_SOURCE: "blue",
  INSUFFICIENT_EVIDENCE: "muted", UNKNOWN: "muted",
};
const sc = (s: string) => `s-${STATE_COLOR[s] || "muted"}`;
const SL: Record<string, string> = {
  REPRESENTATIVE: "REPRESENTATIVE", PARTIALLY_REPRESENTATIVE: "PARTIAL",
  CONCENTRATED: "CONCENTRATED", INSUFFICIENT_EVIDENCE: "NO DATA",
  HIGH_AGREEMENT: "HIGH AGREE", MODERATE_AGREEMENT: "MODERATE",
  LOW_AGREEMENT: "LOW AGREE", INCONSISTENT: "INCONSISTENT",
  FRESH: "FRESH", AGING: "AGING", STALE: "STALE",
  EVIDENCE_READY: "EVIDENCE READY", QUOTE_ONLY: "QUOTE ONLY",
  FRAGMENTED: "FRAGMENTED", SINGLE_SOURCE: "SINGLE SRC",
  STRUCTURALLY_SUPPORTED: "SUPPORTED", CONDITIONAL: "CONDITIONAL",
  CONSTRAINED: "CONSTRAINED", LIMITED_EVIDENCE: "LIMITED", UNKNOWN: "UNKNOWN",
};
const sl = (s: string) => SL[s] || s.replace(/_/g, " ");

type TabId = "audit" | "ai" | "trade" | "stress" | "evidence" | "passport";

// ──────────────────────────────────────────────────────────────────────────────
export default function App() {
  const [input, setInput]           = useState("SOL");
  const [symbol, setSymbol]         = useState("");
  const [loading, setLoading]       = useState(false);
  const [step, setStep]             = useState(0);
  const [report, setReport]         = useState<Report | null>(null);
  const [error, setError]           = useState<string | null>(null);
  const [tab, setTab]               = useState<TabId>("audit");
  const [scenarios, setScenarios]   = useState<StressScenario[]>([]);
  const [stressRes, setStressRes]   = useState<StressResult | null>(null);
  const [stressLoad, setStressLoad] = useState(false);
  const [tradeSize, setTradeSize]   = useState(100000);
  const [tradeSide, setTradeSide]   = useState("BUY");
  const [tradeRes, setTradeRes]     = useState<TradeResult | null>(null);
  const [tradeLoad, setTradeLoad]   = useState(false);
  const [investigation, setInv]     = useState<InvestigationResult | null>(null);
  const [invLoad, setInvLoad]       = useState(false);
  const [evOpen, setEvOpen]         = useState<string | null>(null);
  const [apiOk, setApiOk]           = useState<boolean | null>(null);
  const [demo, setDemo]             = useState(false);
  const timers = useRef<number[]>([]);

  useEffect(() => {
    fetch(`${API}/health`).then(r => r.json())
      .then(d => setApiOk(!!d?.cmc_configured)).catch(() => setApiOk(false));
    fetchScenarios().then(setScenarios).catch(() => {});
  }, []);

  const runAudit = useCallback(async (sym: string, forceDemo = false) => {
    const up = sym.trim().toUpperCase();
    if (!up) return;
    timers.current.forEach(clearTimeout);
    setLoading(true); setReport(null); setError(null); setInv(null);
    setStressRes(null); setTradeRes(null); setTab("audit");
    setSymbol(up); setDemo(forceDemo); setStep(0);
    timers.current = [1,2,3].map((i) =>
      window.setTimeout(() => setStep(i), i * 600) as unknown as number
    );
    try {
      const data = await fetchReport(up, forceDemo);
      setReport(data); setDemo(!!data.is_demo);
    } catch (e: any) {
      // Auto-retry with cached snapshot before showing any error
      try {
        const fallback = await fetchReport(up, true);
        setReport(fallback); setDemo(true);
      } catch {
        setError(e.message);
      }
    }
    finally { timers.current.forEach(clearTimeout); setStep(0); setLoading(false); }
  }, []);

  const runInvestigation = useCallback(async () => {
    if (!report) return;
    setInvLoad(true); setInv(null);
    try { setInv(await fetchInvestigation(symbol, demo)); }
    catch (e: any) { setInv({ verdict: null, model: null, grounded: false, error: e.message }); }
    finally { setInvLoad(false); }
  }, [report, symbol, demo]);

  const runTradeAssess = useCallback(async () => {
    if (!report) return;
    setTradeLoad(true); setTradeRes(null);
    try { setTradeRes(await runTrade(symbol, tradeSize, tradeSide)); }
    catch (e: any) { setError(e.message); }
    finally { setTradeLoad(false); }
  }, [report, symbol, tradeSize, tradeSide]);

  const runStressTest = useCallback(async (s: StressScenario) => {
    if (!report) return;
    setStressLoad(true); setStressRes(null);
    try { setStressRes(await runStress(symbol, s.id)); }
    catch (e: any) { setError(e.message); }
    finally { setStressLoad(false); }
  }, [report, symbol]);

  const gap = report?.reality_gap;

  return (
    <div className="shell">
      {/* ══ SIDEBAR ══════════════════════════════════════════════════════════════ */}
      <aside className="sidebar">
        <div className="sb-logo-row">
          <div className="sb-hex">⬡</div>
          <div>
            <div className="sb-name">MARKETREALITY</div>
            <div className="sb-tag">OS · INTELLIGENCE ENGINE</div>
          </div>
        </div>

        <div className="sb-section">MODULES</div>
        <nav>
          {(["audit","ai","trade","stress","evidence","passport"] as TabId[]).map(t => (
            <button key={t}
              className={`sb-nav ${tab === t ? "sb-nav-on" : ""}`}
              onClick={() => setTab(t)}>
              <span className={`sb-dot ${tab === t ? "dot-on" : ""}`} />
              {t === "audit"    ? "Reality Audit"    :
               t === "ai"      ? "Evidence Investigator"  :
               t === "trade"   ? "Trade Reality"    :
               t === "stress"  ? "Stress Lab"       :
               t === "evidence"? "Evidence"         : "Passport"}
              {t === "ai" && <span className="sb-gem">EV</span>}
            </button>
          ))}
        </nav>

        <div className="sb-spacer" />

        <div className="sb-spacer" />

        <div className={`sb-conn ${apiOk === true ? "conn-ok" : apiOk === false ? "conn-fail" : "conn-wait"}`}>
          <span className="conn-dot" />
          <div>
            <div className="conn-name">MARKET ENGINE</div>
            <div className="conn-st">{apiOk === true ? "Connected" : apiOk === false ? "Offline" : "Checking…"}</div>
          </div>
        </div>
        <div className="sb-ver">v0.3.0 · PRO</div>
      </aside>

      {/* ══ MAIN ═════════════════════════════════════════════════════════════════ */}
      <main className="main">

        {/* Topbar */}
        <header className="topbar">
          <div className="topbar-left">
            <span className="topbar-eye">MARKET INTEGRITY &amp; TRADABILITY INTELLIGENCE ENGINE</span>
            {report && (
              <>
                <span className="topbar-div" />
                <span className="topbar-sym">{report.asset_info?.name || symbol}</span>
                <span className={`topbar-state ${sc(report.status)}`}>{sl(report.status)}</span>
                <span className={`topbar-state ${report.data_mode === "LIVE" ? "s-green" : "s-amber"}`}>
                  {report.data_mode === "LIVE" ? "● LIVE" : "◌ CACHED"}
                </span>
              </>
            )}
          </div>
          <div className="topbar-right">
            <div className={`live-badge ${apiOk ? "live-on" : "live-off"}`}>
              <span className="live-dot" />{apiOk ? "SYSTEM ONLINE" : "SYSTEM DEGRADED"}
            </div>
          </div>
        </header>

        {/* ── Search ─────────────────────────────────────────────────────────── */}
        <div className="search-zone">
          <form className="search-row" onSubmit={e => { e.preventDefault(); runAudit(input); }}>
            <div className="search-box">
              <span className="search-icon">↗</span>
              <input
                className="search-in"
                value={input}
                onChange={e => setInput(e.target.value.toUpperCase())}
                placeholder="Enter symbol  ·  BTC  SOL  ETH  BNB"
                maxLength={10} autoFocus
              />
              <span className="search-hint">SYMBOL</span>
            </div>
            <button type="submit" className="btn-run" disabled={loading}>
              {loading ? "AUDITING…" : "RUN AUDIT →"}
            </button>
          </form>
        </div>

        {/* Progress */}
        {loading && (
          <div className="prog-wrap">
            <div className="prog-track"><div className="prog-bar" style={{ width: `${[0,30,65,90][step]}%` }} /></div>
            <div className="prog-steps">
              {["Fetching quotes", "Fetching market structure", "Running Reality Engine"].map((s, i) => (
                <div key={i} className={`pstep ${step > i ? "ps-done" : step === i+1 ? "ps-active" : ""}`}>
                  <span>{step > i ? "✓" : step === i+1 ? "◌" : "○"}</span>{s}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="err-wrap">
            <div className="err-head">CONNECTION ERROR</div>
            <div className="err-body">
              Could not reach the market data feed for <strong>{symbol || input}</strong>. 
              This is usually a network issue — your ISP may be blocking the API. Try a VPN or check your connection.
            </div>
          </div>
        )}




        {/* ══ WORKSPACE — always visible ══════════════════════════════════════ */}
        {!loading && (
          <div className="workspace">
            {/* Tabs */}
            <div className="tab-row">
              {(["audit","ai","trade","stress","evidence","passport"] as TabId[]).map(t => (
                <button key={t} className={`tab-btn ${tab === t ? "tab-on" : ""}`} onClick={() => setTab(t)}>
                  {t === "audit"    ? "REALITY AUDIT"    :
                   t === "ai"      ? "INVESTIGATION" :
                   t === "trade"   ? "TRADE REALITY"    :
                   t === "stress"  ? "STRESS LAB"       :
                   t === "evidence"? "EVIDENCE"         : "PASSPORT"}
                  {t === "ai" && <span className="tab-gem">EV</span>}
                </button>
              ))}
            </div>

            {/* ── DATA MODE BANNER ── always visible when not LIVE ─────────── */}
            {report && report.data_mode !== "LIVE" && (
              <div className="notice-amber" style={{ margin: "8px 0 0 0", borderRadius: 6, padding: "8px 14px", display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontSize: 16 }}>◌</span>
                <div>
                  <strong>CACHED SNAPSHOT — CMC DATA UNAVAILABLE</strong>
                  <span style={{ marginLeft: 10, opacity: 0.75, fontSize: 11 }}>
                    {report.data_observation} · Snapshot as of {new Date(report.observation_timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            )}

            {/* ── NO REPORT YET — per-tab placeholder ─────────────────────── */}
            {!report && (
              <div className="no-report-state">
                {tab === "audit" && (
                  <div className="nr-prompt">
                    <div className="nr-icon">⬡</div>
                    <div className="nr-title">Enter a symbol above to begin the audit</div>
                    <div className="nr-sub">Type BTC, SOL, ETH, BNB, XRP or any CMC-listed asset and click RUN AUDIT →</div>
                    <div className="quick-chips" style={{ marginTop: 20 }}>
                      {["BTC","SOL","ETH","BNB","XRP","ADA"].map(s => (
                        <button key={s} className="chip" onClick={() => { setInput(s); runAudit(s); }}>{s}</button>
                      ))}
                    </div>
                  </div>
                )}
                {tab === "ai" && (
                  <div className="nr-prompt">
                    <div className="nr-icon">◆</div>
                    <div className="nr-title">Evidence Investigator</div>
                    <div className="nr-sub">Run a Reality Audit first. The investigator reads the evidence objects and writes a deterministic structured market report — every claim cites an evidence ID.</div>
                  </div>
                )}
                {tab === "trade" && (
                  <div className="nr-prompt">
                    <div className="nr-icon">▲</div>
                    <div className="nr-title">Trade Reality</div>
                    <div className="nr-sub">Run a Reality Audit first. Then enter a trade size (e.g. $100K BUY) and get a structural tradability classification with full evidence breakdown.</div>
                  </div>
                )}
                {tab === "stress" && (
                  <div className="nr-prompt">
                    <div className="nr-icon">⚡</div>
                    <div className="nr-title">Stress Lab</div>
                    <div className="nr-sub">Run a Reality Audit first. Then simulate structural shocks — remove the top venue, apply market coverage drops, or run a -20% market shock and see how all dimensions change.</div>
                  </div>
                )}
                {tab === "evidence" && (
                  <div className="nr-prompt">
                    <div className="nr-icon">●</div>
                    <div className="nr-title">Evidence</div>
                    <div className="nr-sub">Run a Reality Audit first. Every finding will appear here as a traceable evidence object — showing the source CMC endpoint, the calculation used, the sample size, and the limitation.</div>
                  </div>
                )}
                {tab === "passport" && (
                  <div className="nr-prompt">
                    <div className="nr-icon">⬡</div>
                    <div className="nr-title">Market Passport</div>
                    <div className="nr-sub">Run a Reality Audit first. The Passport is the final audit snapshot — all structural dimensions, headline data, and evidence quality in one shareable view.</div>
                  </div>
                )}
              </div>
            )}

            {/* ════ REALITY AUDIT ══════════════════════════════════════════════ */}
            {tab === "audit" && report && (
              <div className="audit-layout">

                {/* Row 1: Identity + Gap + Global */}
                <div className="top-grid">
                  {/* Identity card */}
                  <div className="card">
                    <div className="eyebrow">ASSET IDENTITY</div>
                    <div className="id-row">
                      <div className="id-icon">{symbol[0]}</div>
                      <div>
                        <div className="id-sym">{symbol}</div>
                        <div className="id-name">{report.asset_info?.name}</div>
                        {report.asset_info?.cmc_rank && (
                          <div className="id-rank">CMC #{report.asset_info.cmc_rank}</div>
                        )}
                      </div>
                      <div className={`state-pill ${sc(report.status)}`}>{sl(report.status)}</div>
                    </div>

                    <div className="price-grid">
                      <Metric label="PRICE"      value={f.price(gap?.headline_price)}
                        sub={<Chg v={gap?.pct_change_24h} label="24h" />} />
                      <Metric label="MARKET CAP" value={f.usd(gap?.headline_market_cap)}
                        sub={<span className="muted">{gap?.market_cap_dominance?.toFixed(2)}% dom.</span>} />
                      <Metric label="VOLUME 24H" value={f.usd(gap?.headline_volume_24h)}
                        sub={<Chg v={gap?.pct_change_1h} label="1h" />} />
                    </div>

                    {gap?.cex_volume_24h != null && gap.headline_volume_24h != null && (
                      <div className="split-section">
                        <div className="split-labels">
                          <span>CEX {f.usd(gap.cex_volume_24h)}</span>
                          <span>DEX {f.usd(gap.dex_volume_24h)}</span>
                        </div>
                        <div className="split-bar">
                          <div className="split-cex" style={{ width: `${((gap.cex_volume_24h / gap.headline_volume_24h) * 100).toFixed(1)}%` }} />
                          <div className="split-dex" style={{ width: `${(((gap.dex_volume_24h ?? 0) / gap.headline_volume_24h) * 100).toFixed(1)}%` }} />
                        </div>
                        <div className="split-note">CEX / DEX volume split</div>
                      </div>
                    )}

                    <div className="chg-strip">
                      {([["1H",gap?.pct_change_1h],["24H",gap?.pct_change_24h],["7D",gap?.pct_change_7d]] as [string,number|undefined][]).map(([l,v]) => (
                        <div key={l} className="chg-cell">
                          <div className="chg-lbl">{l}</div>
                          <div className={`chg-val ${(v ?? 0) >= 0 ? "pos" : "neg"}`}>{f.pct(v)}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Gap card */}
                  <div className="card">
                    <div className="eyebrow">REALITY GAP</div>
                    <p className="card-desc">
                      {report.status === "QUOTE_ONLY"
                        ? "Headline data confirmed. Full pair-structure analysis requires CMC Standard plan."
                        : report.status === "EVIDENCE_READY"
                        ? "Full structural evidence gathered from live market-pair data."
                        : "Insufficient pair-level evidence observed."}
                    </p>
                    <KVList rows={[
                      ["Price",            f.price(gap?.headline_price)],
                      ["Volume 24h",       f.usd(gap?.headline_volume_24h)],
                      ["Market Cap",       f.usd(gap?.headline_market_cap)],
                      ["Circulating Sup.", `${f.num(gap?.circulating_supply)} ${symbol}`],
                      ["CMC Pairs Listed", f.num(gap?.num_market_pairs_cmc)],
                      ["Observed Pairs",   `${gap?.observed_pair_count ?? 0} (this audit)`],
                      ["Coverage",         sl(gap?.coverage_state ?? "INSUFFICIENT_EVIDENCE")],
                    ]} />
                    {report.status === "QUOTE_ONLY" && (
                      <div className="notice-amber">⚠ Market-pairs endpoint requires CMC Standard plan+.</div>
                    )}
                  </div>

                  {/* Global */}
                  {report.global_context && (
                    <div className="card">
                      <div className="eyebrow">GLOBAL MARKET</div>
                      <KVList rows={[
                        ["Total Market Cap", f.usd(report.global_context.total_market_cap_usd)],
                        ["24h Volume",       f.usd(report.global_context.total_volume_24h_usd)],
                        ["Active Cryptos",   f.num(report.global_context.active_cryptocurrencies)],
                        ["Active Exchanges", f.num(report.global_context.active_exchanges)],
                        ["Last Updated",     f.ts(report.global_context.last_updated)],
                      ]} />
                      <div style={{ marginTop: 10 }}>
                        <DomBar label="BTC" pct={report.global_context.btc_dominance ?? 0} color="var(--amber)" />
                        <DomBar label="ETH" pct={report.global_context.eth_dominance ?? 0} color="var(--teal)" />
                      </div>
                    </div>
                  )}
                </div>

                {/* Dimensions */}
                <SectionLabel>STRUCTURAL DIMENSIONS</SectionLabel>
                <div className="dim-grid">
                  {report.dimensions.map(d => (
                    <div key={d.name} className={`dim-card dim-${STATE_COLOR[d.state] || "muted"}`}>
                      <div className="dim-name">{d.name.toUpperCase()}</div>
                      <div className={`dim-state ${sc(d.state)}`}>{sl(d.state)}</div>
                      <div className="dim-val">{d.display_value || "—"}</div>
                      <div className="dim-desc">{d.description}</div>
                    </div>
                  ))}
                </div>

                {/* Venues */}
                {report.venues.length > 0 && (
                  <>
                    <SectionLabel>VENUE BREAKDOWN</SectionLabel>
                    <div className="card pad-0">
                      <table className="tbl">
                        <thead><tr>
                          <th>#</th><th>VENUE</th><th>TYPE</th>
                          <th>PAIRS</th><th>VOLUME 24H</th><th>SHARE</th><th>BAR</th>
                        </tr></thead>
                        <tbody>
                          {report.venues.slice(0,12).map((v,i) => (
                            <tr key={v.name}>
                              <td className="muted">{i+1}</td>
                              <td className="bold">{v.name}</td>
                              <td><span className={`tag ${v.market_type==="CEX"?"tag-cex":v.market_type==="DEX"?"tag-dex":""}`}>{v.market_type}</span></td>
                              <td className="mono">{v.pair_count}</td>
                              <td className="mono">{f.usd(v.total_volume_24h_usd)}</td>
                              <td className="mono">{f.ratio(v.volume_share)}</td>
                              <td><div className="vol-bar"><div className="vol-fill" style={{ width:`${(v.volume_share*100).toFixed(1)}%` }} /></div></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}

                <div className="limits-row">
                  {report.limitations.map((l,i) => <div key={i} className="limit">· {l}</div>)}
                </div>
              </div>
            )}

            {/* ════ EVIDENCE INVESTIGATION ══════════════════════════════════════════ */}
            {tab === "ai" && report && (
              <div className="ai-wrap">
                <div className="card">
                  <div className="eyebrow">EVIDENCE INVESTIGATOR · DETERMINISTIC ANALYSIS</div>
                  <p className="card-desc">
                    The Evidence Investigator reads the evidence objects from this audit and writes a structured market integrity report.
                    Every claim cites a specific evidence ID. If no supporting evidence exists, no claim is made.
                    <br /><span className="muted" style={{fontSize:11}}>Powered by the deterministic MarketReality Engine.</span>
                  </p>
                  {!investigation && (
                    <button className="btn-run" onClick={runInvestigation} disabled={invLoad} style={{ marginTop: 12 }}>
                      {invLoad ? "INVESTIGATING…" : "◆ RUN INVESTIGATION"}
                    </button>
                  )}
                  {invLoad && (
                    <div className="ai-loading">
                      <div className="ai-spin">◆</div>
                      <div>Engine is analyzing {report.evidence.length} evidence objects…</div>
                    </div>
                  )}
                  {investigation && (
                    <div className="ai-result">
                      <div className="ai-meta">
                        <span className="ai-model">
                          {investigation.model ? `◆ ${investigation.model}` : "◆ ENGINE"}
                        </span>
                        <span className={`ai-grounded ${investigation.grounded ? "grounded-ok" : "grounded-no"}`}>
                          {investigation.grounded ? "✓ Evidence-grounded" : "⚠ Not grounded"}
                        </span>
                        {investigation.is_demo && <span className="demo-pill">DEMO DATA</span>}
                      </div>
                      {investigation.error && (
                        <div className="ai-error">
                          <div className="err-head">INVESTIGATION FAILED</div>
                          <div className="err-body">{investigation.error}</div>
                        </div>
                      )}
                      {investigation.verdict && (
                        <div className="ai-verdict">
                          {investigation.verdict.split("\n").map((line, i) => {
                            const trimmed = line.trim();
                            if (trimmed.startsWith("**") && trimmed.endsWith("**")) {
                              return <div key={i} className="ai-section-head">{trimmed.replace(/\*\*/g, "")}</div>;
                            }
                            if (trimmed.startsWith("-") || trimmed.startsWith("•")) {
                              return <div key={i} className="ai-bullet">{trimmed.replace(/^[-•]\s*/, "")}</div>;
                            }
                            if (!trimmed) return <div key={i} className="ai-gap" />;
                            return <div key={i} className="ai-para">{trimmed}</div>;
                          })}
                        </div>
                      )}
                      <div className="ai-actions">
                        <button className="btn-demo-sm" onClick={runInvestigation}>↺ Re-run</button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ════ TRADE REALITY ═════════════════════════════════════════════ */}
            {tab === "trade" && report && (
              <div className="trade-wrap">
                <div className="card">
                  <div className="eyebrow">STRUCTURAL TRADABILITY ASSESSMENT</div>
                  <p className="card-desc">
                    Structural assessment based on observed market structure — not an execution quote or slippage model.
                  </p>
                  <div className="trade-ctl">
                    <Field label="SIDE">
                      <select value={tradeSide} onChange={e => setTradeSide(e.target.value)}>
                        <option>BUY</option><option>SELL</option>
                      </select>
                    </Field>
                    <Field label="TRADE SIZE (USD)">
                      <select value={tradeSize} onChange={e => setTradeSize(Number(e.target.value))}>
                        {[10000,50000,100000,500000,1000000,5000000,10000000].map(s => (
                          <option key={s} value={s}>{f.usd(s)}</option>
                        ))}
                      </select>
                    </Field>
                    <button className="btn-run" onClick={runTradeAssess} disabled={tradeLoad}>
                      {tradeLoad ? "ASSESSING…" : "ASSESS →"}
                    </button>
                  </div>
                  {tradeRes && (
                    <div className="trade-result">
                      <div className="trade-head">
                        <div>
                          <div className="eyebrow">VERDICT</div>
                          <div className={`verdict ${sc(tradeRes.result)}`}>{sl(tradeRes.result)}</div>
                        </div>
                        <div className="trade-order mono">{tradeSide} {f.usd(tradeSize)} {symbol}</div>
                      </div>
                      {tradeRes.dimensions.map(d => (
                        <div key={d.name} className="trade-dim">
                          <span className="muted">{d.name}</span>
                          <span className={sc(d.state)}>{sl(d.state)}</span>
                          {d.display_value && <span className="mono muted">{d.display_value}</span>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ════ STRESS LAB ════════════════════════════════════════════════ */}
            {tab === "stress" && report && (
              <div className="stress-wrap">
                <div className="stress-list">
                  <div className="eyebrow" style={{ marginBottom: 8 }}>STRESS SCENARIOS</div>
                  {scenarios.length === 0 && <div className="muted" style={{ fontSize: 11 }}>No scenarios loaded.</div>}
                  {scenarios.map(s => (
                    <button key={s.id} className="scenario" onClick={() => runStressTest(s)} disabled={stressLoad}>
                      <div className="sc-id">{s.id}</div>
                      <div className="sc-name">{s.name}</div>
                      <div className="sc-desc">{s.description}</div>
                    </button>
                  ))}
                </div>
                {stressRes && (
                  <div className="card stress-out">
                    <div className="eyebrow">{stressRes.scenario.name}</div>
                    <div className="stress-compare">
                      <div>
                        <div className="stress-col-lbl">BEFORE</div>
                        {Object.entries(stressRes.before).slice(0,8).map(([k,v]) => (
                          <div key={k} className="kv"><span className="muted">{k.replace(/_/g," ")}</span><span className="mono">{typeof v==="number" ? v.toFixed(3) : String(v??"—")}</span></div>
                        ))}
                      </div>
                      <div className="stress-arrow">→</div>
                      <div>
                        <div className="stress-col-lbl">AFTER</div>
                        {Object.entries(stressRes.after).slice(0,8).map(([k,v]) => (
                          <div key={k} className="kv"><span className="muted">{k.replace(/_/g," ")}</span><span className="mono">{typeof v==="number" ? v.toFixed(3) : String(v??"—")}</span></div>
                        ))}
                      </div>
                    </div>
                    {stressRes.affected_dimensions.length > 0 && (
                      <div className="affected">
                        <span className="eyebrow" style={{fontSize:7}}>AFFECTED: </span>
                        {stressRes.affected_dimensions.map(d => <span key={d} className="aff-tag">{d}</span>)}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ════ EVIDENCE ══════════════════════════════════════════════════ */}
            {tab === "evidence" && report && (
              <div className="ev-wrap">
                <div className="eyebrow" style={{ marginBottom: 8 }}>
                  {report.evidence.length} EVIDENCE OBJECTS · {report.cmc_endpoints_used.length} CMC ENDPOINTS
                </div>
                {report.evidence.map(ev => (
                  <div key={ev.evidence_id}
                    className={`ev-card ${evOpen === ev.evidence_id ? "ev-open" : ""}`}
                    onClick={() => setEvOpen(evOpen === ev.evidence_id ? null : ev.evidence_id)}>
                    <div className="ev-head">
                      <span className="ev-id">{ev.evidence_id}</span>
                      <span className="ev-find">{ev.finding.replace(/_/g," ")}</span>
                      <span className="ev-val mono">{ev.value != null ? String(ev.value) : "—"} {ev.unit||""}</span>
                    </div>
                    {evOpen === ev.evidence_id && (
                      <div className="ev-body">
                        <EVR k="Source" v={ev.source_endpoint} />
                        <EVR k="Calculation" v={ev.calculation} />
                        {ev.sample_size != null && <EVR k="Sample" v={String(ev.sample_size)} />}
                        {ev.source_timestamp && <EVR k="Time" v={f.ts(ev.source_timestamp)} />}
                        {ev.limitation && <EVR k="Limitation" v={ev.limitation} />}
                      </div>
                    )}
                  </div>
                ))}
                <div className="ev-endpoints">
                  <div className="eyebrow" style={{ marginBottom: 5 }}>ENDPOINTS USED</div>
                  {report.cmc_endpoints_used.map(e => <div key={e} className="endpoint">{e}</div>)}
                </div>
              </div>
            )}

            {/* ════ PASSPORT ══════════════════════════════════════════════════ */}
            {tab === "passport" && report && (
              <div className="passport-wrap">
                <div className="card passport-card">
                  <div className="pass-head">
                    <div className="pass-title">MARKET PASSPORT</div>
                    <div className="pass-asset">{report.asset_info?.name || symbol} · {symbol}</div>
                    <div className="pass-ts">{new Date(report.observation_timestamp).toLocaleString()}</div>
                    {demo && <span className="demo-pill" style={{ marginTop: 6, display:"inline-block" }}>⬡ DEMO DATA</span>}
                  </div>
                  <div className="pass-grid">
                    <div className="pass-col">
                      <PS title="HEADLINE DATA">
                        {[
                          ["Price",f.price(gap?.headline_price)],
                          ["Market Cap",f.usd(gap?.headline_market_cap)],
                          ["Volume 24h",f.usd(gap?.headline_volume_24h)],
                          ["CEX Volume",f.usd(gap?.cex_volume_24h)],
                          ["DEX Volume",f.usd(gap?.dex_volume_24h)],
                          ["Change 1h",f.pct(gap?.pct_change_1h)],
                          ["Change 24h",f.pct(gap?.pct_change_24h)],
                          ["Change 7d",f.pct(gap?.pct_change_7d)],
                          ["Dominance",gap?.market_cap_dominance != null ? `${gap.market_cap_dominance.toFixed(2)}%` : "—"],
                          ["Circulating",f.num(gap?.circulating_supply)],
                        ].map(([k,v]) => <KVR key={k} k={k} v={v} />)}
                      </PS>
                      <PS title="AUDIT METADATA">
                        {[
                          ["Overall Status", sl(report.status)],
                          ["Data Mode", report.data_mode],
                          ["Data Source", report.data_observation],
                          ["Observed Pairs", String(gap?.observed_pair_count??0)],
                          ["CMC Rank", report.asset_info?.cmc_rank ? `#${report.asset_info.cmc_rank}` : "—"],
                          ["Evidence Objects", String(report.evidence.length)],
                          ["Endpoints Used", String(report.cmc_endpoints_used.length)],
                        ].map(([k,v]) => <KVR key={k} k={k} v={v} />)}
                      </PS>
                    </div>
                    <div className="pass-col">
                      <PS title="STRUCTURAL DIMENSIONS">
                        {report.dimensions.map(d => <KVR key={d.name} k={d.name} v={`${sl(d.state)} · ${d.display_value||"—"}`} />)}
                      </PS>
                      <PS title="LIMITATIONS">
                        {report.limitations.map((l,i) => <div key={i} className="limit">· {l}</div>)}
                      </PS>
                    </div>
                  </div>
                  <div className="pass-footer">
                    EVIDENCE DECIDES. · MARKETREALITY OS · CMC-NATIVE
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        <footer className="footer">
          <span>CMC-NATIVE · EVIDENCE-FIRST · DETERMINISTIC CORE</span>
          <span>NO EVIDENCE → NO CLAIM</span>
        </footer>
      </main>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────
function Metric({ label, value, sub }: { label: string; value: string; sub: React.ReactNode }) {
  return <div className="metric"><div className="m-lbl">{label}</div><div className="m-val">{value}</div><div className="m-sub">{sub}</div></div>;
}
function Chg({ v, label }: { v?: number | null; label: string }) {
  return <span className={(v ?? 0) >= 0 ? "pos" : "neg"}>{f.pct(v)} {label}</span>;
}
function SectionLabel({ children }: { children: React.ReactNode }) {
  return <div className="section-lbl">{children}</div>;
}
function KVList({ rows }: { rows: [string, string][] }) {
  return <div className="kvl">{rows.map(([k, v]) => <div key={k} className="kv"><span className="kv-k">{k}</span><span className="kv-v mono">{v}</span></div>)}</div>;
}
function KVR({ k, v }: { k: string; v: string }) {
  return <div className="kv"><span className="kv-k">{k}</span><span className="kv-v mono">{v}</span></div>;
}
function DomBar({ label, pct, color }: { label: string; pct: number; color: string }) {
  return (
    <div className="dom-row">
      <span className="dom-lbl">{label}</span>
      <div className="dom-track"><div className="dom-fill" style={{ width:`${pct.toFixed(1)}%`, background: color }} /></div>
      <span className="dom-pct">{pct.toFixed(1)}%</span>
    </div>
  );
}
function EVR({ k, v }: { k: string; v: string }) {
  return <div className="ev-row"><span className="ev-k">{k}</span><span className="ev-v mono">{v}</span></div>;
}
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="field"><label>{label}</label>{children}</div>;
}
function PS({ title, children }: { title: string; children: React.ReactNode }) {
  return <div className="pass-sec"><div className="pass-sec-t">{title}</div>{children}</div>;
}
