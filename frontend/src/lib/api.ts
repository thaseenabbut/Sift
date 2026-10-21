import type { SearchResponse } from '../types/search'

export async function searchSift(query: string, page = 1): Promise<SearchResponse> {

  const params = new URLSearchParams({
    q: query,
    page: String(page),
  })

  const response = await fetch(
    `http://127.0.0.1:8000/search?${params.toString()}`
  )

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(
      error?.detail ?? `Search failed (${response.status})`
    )
  }

  return response.json()
}
