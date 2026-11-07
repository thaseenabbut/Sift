import type { SearchResponse } from '../types/search'

const API_URL = import.meta.env.VITE_API_URL

export async function searchSift(query: string, page = 1): Promise<SearchResponse> {

  const params = new URLSearchParams({
    q: query,
    page: String(page),
  })

  const response = await fetch(
    `${API_URL}/search?${params.toString()}`
  )

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(
      error?.detail ?? `Search failed (${response.status})`
    )
  }

  return response.json()
}
