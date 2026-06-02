/**
 * Returns a colour string for a 0–1 confidence value.
 * Used in both ResultCard and the main screen's confidenceColor derived value.
 */
export function confidenceColor(conf) {
  if (conf == null) return "#94A3B8";
  if (conf > 0.8) return "#34D399";
  if (conf > 0.5) return "#FBBF24";
  return "#F87171";
}

/**
 * Finer-grained colour scale used inside each result row.
 *   >= 0.7  → green
 *   >= 0.45 → amber
 *   <  0.45 → red
 */
export function rowConfidenceColor(conf) {
  if (conf >= 0.7) return "#22c55e";
  if (conf >= 0.45) return "#f59e0b";
  return "#ef4444";
}

export function confidencePercent(conf) {
  return `${Math.round((conf ?? 0) * 100)}%`;
}
