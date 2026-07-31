import type { RetrievedSource } from '@/types/chat'

export type ScoreDisplayKind = 'similarity' | 'relevance'

export type FormattedSourceScore = {
  label: string
  kind: ScoreDisplayKind
}

/** Cross-encoder and other rerankers emit raw logits — not user-friendly as-is. */
function usesRelativeRelevance(scores: number[]) {
  return scores.some((score) => score > 1 || score < 0)
}

function toRelativePercent(score: number, min: number, max: number) {
  if (max === min) {
    return 100
  }
  return Math.round(((score - min) / (max - min)) * 100)
}

/**
 * Format retrieval scores for display.
 * - Vector / hybrid (0–1): show as similarity %
 * - Cross-encoder logits: min–max normalize within the result set → relevance %
 */
export function formatSourceScoresForDisplay(sources: Pick<RetrievedSource, 'score'>[]): FormattedSourceScore[] {
  if (sources.length === 0) {
    return []
  }

  const scores = sources.map((source) => source.score)

  if (usesRelativeRelevance(scores)) {
    const min = Math.min(...scores)
    const max = Math.max(...scores)
    return scores.map((score) => ({
      kind: 'relevance' as const,
      label: `${toRelativePercent(score, min, max)}% relevance`,
    }))
  }

  return scores.map((score) => ({
    kind: 'similarity' as const,
    label: `${Math.round(score * 100)}% similar`,
  }))
}

export function scoreDisplayFootnote(sources: Pick<RetrievedSource, 'score'>[]) {
  const scores = sources.map((source) => source.score)
  if (usesRelativeRelevance(scores)) {
    return 'Relevance is normalized within this result set (top hit = 100%).'
  }
  return 'Similarity from vector / hybrid retrieval (higher = closer match).'
}
