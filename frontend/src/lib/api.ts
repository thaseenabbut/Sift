import type { SearchResponse } from '../types/search'

export async function searchSift(query: string): Promise<SearchResponse> {
  const started = performance.now()

  const response = await fetch(
    `http://127.0.0.1:8000/search?q=${encodeURIComponent(query)}`
  )

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(
      error?.detail ?? `Search failed (${response.status})`
    )
  }

  const data = await response.json()

  return {
    ...data,
    tookMs: Math.round(performance.now() - started),
  }
}
