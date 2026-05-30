// Small presentation helpers shared across components.

/** Format an INR amount as a compact lakh string, e.g. 250000 -> "₹2.5L". */
export function formatLakh(inr: number): string {
  const lakhs = inr / 100000;
  const rounded = Number.isInteger(lakhs) ? lakhs.toString() : lakhs.toFixed(1);
  return `₹${rounded}L`;
}

/** Price range as "₹0.9L–₹2.5L". */
export function formatPriceRange(min: number, max: number): string {
  return `${formatLakh(min)}–${formatLakh(max)}`;
}

/** Cosine similarity 0..1 -> "84% match". */
export function formatMatch(score: number): string {
  return `${Math.round(score * 100)}% match`;
}

/** Title-case a single word, e.g. "honeymoon" -> "Honeymoon". */
export function titleCase(word: string): string {
  return word.charAt(0).toUpperCase() + word.slice(1);
}

/** Short month label, e.g. "december" -> "Dec". */
export function shortMonth(month: string): string {
  return titleCase(month).slice(0, 3);
}
