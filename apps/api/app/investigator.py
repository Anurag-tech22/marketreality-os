"""MarketReality OS – Evidence Investigator.

Generates a structured market integrity report from evidence objects.

Architecture:
1. Deterministic MarketReality Engine (always runs, no external API needed)
2. CMC AI Context (optional enrichment when CMC_PRO_API_KEY supports /v5/cmc-ai)

Gemini has been removed. The core application has ZERO dependency on any
external AI service. CMC AI is pure optional enrichment.
"""
from __future__ import annotations

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger("marketreality.investigator")


# ── Deterministic Evidence Investigator ──────────────────────────────
# This is the primary intelligence layer. It is reproducible, traceable,
# and produces output strictly from the evidence objects passed to it.

def _rule_based_investigation(report: dict) -> str:
    """Generate a deterministic, evidence-grounded investigation report.

    Every finding in this report must reference a specific evidence ID.
    No claims are made without supporting evidence.
    """
    asset   = report.get("asset", "UNKNOWN")
    status  = report.get("status", "UNKNOWN")
    gap     = report.get("reality_gap", {}) or {}
    dims    = report.get("dimensions", [])
    evidence = report.get("evidence", [])
    venues  = report.get("venues", [])

    price      = gap.get("headline_price")
    vol        = gap.get("headline_volume_24h")
    mcap       = gap.get("headline_market_cap")
    top5       = gap.get("top5_concentration")
    top1       = gap.get("top1_venue_share")
    pct24      = gap.get("pct_change_24h")
    pairs      = gap.get("observed_pair_count", 0)
    dispersion = gap.get("price_dispersion_pct")
    num_pairs_cmc = gap.get("num_market_pairs_cmc")

    # Build state lookup
    dim_map     = {d["name"]: d for d in dims}
    price_state = dim_map.get("Price Agreement",      {}).get("state", "UNKNOWN")
    vol_state   = dim_map.get("Volume Concentration", {}).get("state", "UNKNOWN")
    venue_state = dim_map.get("Venue Dependence",     {}).get("state", "UNKNOWN")
    fresh_state = dim_map.get("Data Freshness",       {}).get("state", "UNKNOWN")
    cover_state = dim_map.get("Market Coverage",      {}).get("state", "UNKNOWN")

    # Find evidence IDs for citation
    ev_map   = {e["finding"]: e["evidence_id"] for e in evidence}
    price_ev = ev_map.get("headline_price",               "EV-?")
    vol_ev   = ev_map.get("top_5_volume_concentration",   "EV-?")
    pair_ev  = ev_map.get("observed_market_pairs",        "EV-?")
    fresh_ev = ev_map.get("data_freshness_median_seconds","EV-?")

    # Verdict from dimension states
    BAD_STATES = {"CONCENTRATED","CONSTRAINED","STALE","FRAGMENTED","LOW_AGREEMENT","INSUFFICIENT"}
    bad_count  = sum(1 for d in dims if d.get("state") in BAD_STATES)

    if bad_count == 0:
        verdict = (
            f"{asset} shows strong structural integrity across all observed CMC-tracked dimensions. "
            f"Pricing is consistent across venues and market coverage is representative of observed activity."
        )
    elif bad_count <= 2:
        verdict = (
            f"{asset} exhibits adequate structural integrity with notable concentration risk "
            f"in {bad_count} dimension(s). The market is functional but traders should "
            f"be aware of venue dependency before executing large orders."
        )
    else:
        verdict = (
            f"{asset} shows significant structural fragility across {bad_count} dimensions. "
            f"High concentration, limited coverage, or stale data create material execution risk "
            f"that is not reflected in headline CMC metrics."
        )

    # Formatters
    price_str = f"${price:,.4f}" if price else "N/A"
    vol_str   = f"${vol/1e9:.2f}B" if vol else "N/A"
    mcap_str  = f"${mcap/1e9:.1f}B" if mcap else "N/A"
    pct_str   = f"{pct24:+.2f}%" if pct24 is not None else "N/A"
    top5_str  = f"{top5*100:.1f}%" if top5 else "N/A"
    top1_str  = f"{top1*100:.1f}%" if top1 else "N/A"
    disp_str  = f"{dispersion:.3f}%" if dispersion else "N/A"

    # Key findings — each cites a specific evidence ID
    findings = []
    if price:
        findings.append(
            f"• CMC headline price: {price_str} (24h: {pct_str}). "
            f"Cross-venue price dispersion: {disp_str}. [{price_ev}]"
        )
    if vol and pairs:
        cov_note = ""
        if num_pairs_cmc and pairs < num_pairs_cmc:
            cov_pct = (pairs / num_pairs_cmc) * 100
            cov_note = f" CMC reports {num_pairs_cmc:,} total pairs; this audit observed {pairs:,} ({cov_pct:.0f}% coverage)."
        findings.append(
            f"• CMC-observed 24h volume: {vol_str} across {pairs:,} market pairs.{cov_note} [{pair_ev}]"
        )
    if top5:
        conc_label = "HIGH" if (top5 or 0) > 0.7 else "MODERATE" if (top5 or 0) > 0.5 else "LOW"
        findings.append(
            f"• Volume concentration is {conc_label}: top-5 pairs account for {top5_str} of observed flow. [{vol_ev}]"
        )
    if top1:
        findings.append(
            f"• Largest venue controls {top1_str} of observed volume. [{vol_ev}]"
        )
    if venues:
        top_v = venues[0]["name"] if venues else "Unknown"
        venue_diversity = "adequate" if len(venues) >= 5 else "limited"
        findings.append(
            f"• Primary liquidity anchor: {top_v}. "
            f"Venue diversity is {venue_diversity} ({len(venues)} venues observed). [{pair_ev}]"
        )

    if not findings:
        findings.append("• Insufficient evidence to generate findings. CMC data may be unavailable or plan-limited.")

    # Structural risks
    risks = []
    if (top1 or 0) > 0.4:
        risks.append(
            f"• HIGH CONCENTRATION: Single venue controls {top1_str} of observed volume. "
            f"Venue disruption would materially impact observable liquidity."
        )
    elif (top1 or 0) > 0.25:
        risks.append(
            f"• MODERATE CONCENTRATION: Top venue at {top1_str}. Monitor for fragmentation if this venue de-lists."
        )
    if (top5 or 0) > 0.7:
        risks.append(
            "• TAIL RISK: Volume is highly concentrated in a narrow set of pairs. "
            "Secondary venues lack sufficient observable depth."
        )
    if fresh_state in ("STALE", "AGING"):
        risks.append(
            f"• DATA FRESHNESS DEGRADED ({fresh_state}): "
            f"Some observed pair data may not reflect current market conditions. [{fresh_ev}]"
        )
    if cover_state not in ("REPRESENTATIVE",):
        risks.append(
            f"• COVERAGE: Observed market state is {cover_state}. "
            f"Structural analysis may underrepresent total global activity."
        )
    if not risks:
        risks.append("• No major structural risks identified within the current CMC observation window.")

    # Structural tradability statement
    if bad_count == 0:
        trade_stmt = (
            f"Structural tradability assessment: {asset} appears sound for standard execution sizes "
            f"based on observed venue distribution and volume concentration. "
            f"This is a structural assessment only — not an execution quote."
        )
    elif (top1 or 0) > 0.4:
        trade_stmt = (
            f"Structural tradability assessment: Execution is feasible but routing is critical. "
            f"Over-reliance on the primary venue ({top1_str} share) "
            f"creates concentration risk for large orders. "
            f"This is a structural assessment only — not an execution quote."
        )
    else:
        trade_stmt = (
            f"Structural tradability assessment: Conditional. Standard orders are structurally supported "
            f"on primary venues, but large block trades require careful routing due to concentration risk. "
            f"This is a structural assessment only — not an execution quote."
        )

    data_note = (
        "\n\n_Source: CMC-observed market data. All findings reference specific evidence IDs above. "
        "Calculations are deterministic and reproducible. No claims are made beyond what the evidence supports._"
    )

    lines = [
        "**MARKET INTEGRITY VERDICT**",
        verdict,
        "",
        "**KEY FINDINGS**",
        *findings[:6],
        "",
        "**STRUCTURAL RISKS**",
        *risks[:4],
        "",
        "**STRUCTURAL TRADABILITY**",
        trade_stmt,
        data_note,
    ]
    return "\n".join(lines)


# ── CMC AI context (optional, plan-dependent) ─────────────────────
# CMC AI provides market context/narratives — NOT structural calculations.
# It is called ONLY when explicitly requested and only if plan supports it.

async def _fetch_cmc_ai_context(symbol: str) -> dict | None:
    """Fetch optional CMC AI contextual intelligence.

    Uses /v5/cmc-ai/latest if the CMC plan supports it.
    Returns None gracefully if unavailable or plan-limited.
    """
    if not settings.cmc_pro_api_key:
        return None
    try:
        import httpx
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=4.0)) as client:
            r = await client.get(
                f"{settings.cmc_base_url}/v5/cmc-ai/latest",
                params={"symbol": symbol},
                headers={
                    "X-CMC_PRO_API_KEY": settings.cmc_pro_api_key,
                    "Accept": "application/json",
                },
            )
            if r.status_code == 200:
                data = r.json()
                ai_data = data.get("data", {})
                if ai_data:
                    return {
                        "source": "CMC AI /v5/cmc-ai/latest",
                        "content": ai_data,
                        "available": True,
                    }
            elif r.status_code in (401, 403):
                logger.info("CMC AI endpoint plan-limited (status %d)", r.status_code)
                return {"available": False, "reason": "PLAN_LIMITED"}
            else:
                logger.warning("CMC AI returned status %d", r.status_code)
                return {"available": False, "reason": f"HTTP_{r.status_code}"}
    except Exception as exc:
        logger.warning("CMC AI fetch failed: %s", exc)
        return {"available": False, "reason": "UNAVAILABLE"}


# ── Primary entry point ───────────────────────────────────────────

async def run_investigation(report: dict) -> dict:
    """Run the Evidence Investigator over a RealityReport.

    Architecture:
    1. Always runs the deterministic MarketReality Engine.
    2. Optionally fetches CMC AI context if the plan supports it.
    3. Returns structured result with full traceability.

    Returns: { verdict, model, grounded, error, cmc_ai_context }
    """
    verdict = _rule_based_investigation(report)
    logger.info("Deterministic investigation complete for %s", report.get("asset"))
    return {
        "verdict": verdict,
        "model": "MarketReality Deterministic Engine v2",
        "grounded": True,
        "error": None,
        "cmc_ai_context": None,  # Fetched separately on demand
    }


# Keep old name as alias for backward compatibility with existing route handlers
async def run_ai_investigation(report: dict) -> dict:
    """Backward-compatible alias. Calls run_investigation."""
    return await run_investigation(report)
