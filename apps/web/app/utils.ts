/**
 * MarketReality OS – Formatting utilities.
 */

export function formatUsd(value: number | null | undefined): string {
  if (value == null) return "—";
  if (value >= 1_000_000_000_000) return `$${(value / 1_000_000_000_000).toFixed(2)}T`;
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`;
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(2)}`;
}

export function formatPct(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null) return "—";
  return value.toLocaleString();
}

export function stateColor(state: string): string {
  const s = state.toUpperCase();
  if (["REPRESENTATIVE", "HIGH_AGREEMENT", "FRESH", "SUFFICIENT", "HIGH",
       "STRUCTURALLY_SUPPORTED", "EVIDENCE_READY", "CONSISTENT", "LOW"].includes(s))
    return "var(--state-good)";
  if (["PARTIALLY_REPRESENTATIVE", "MODERATE_AGREEMENT", "AGING", "LIMITED",
       "MODERATE", "CONDITIONAL", "LIMITED_EVIDENCE", "MEDIUM"].includes(s))
    return "var(--state-warn)";
  if (["CONCENTRATED", "INCONSISTENT", "STALE", "INSUFFICIENT", "CONSTRAINED",
       "FRAGMENTED", "INSUFFICIENT_EVIDENCE"].includes(s))
    return "var(--state-bad)";
  return "var(--text-muted)";
}

export function stateLabel(state: string): string {
  return state.replace(/_/g, " ");
}
