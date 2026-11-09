import type { SearchResponse } from '../types/search'

const API_URL = import.meta.env.VITE_API_URL

export class ApiError extends Error {
  status: number
  retryAfter?: number

  constructor(status: number, message: string, retryAfter?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.retryAfter = retryAfter
    Object.setPrototypeOf(this, ApiError.prototype)
  }
}

export async function searchSift(query: string, page = 1): Promise<SearchResponse> {
  const params = new URLSearchParams({
    q: query,
    page: String(page),
  })

  let response: Response
  try {
    response = await fetch(
      `${API_URL}/search?${params.toString()}`
    )
  } catch {
    // Network failure (server down, connection refused, offline)
    throw new ApiError(503, 'Search service is temporarily unavailable.')
  }

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    const retryAfterHeader = response.headers.get('Retry-After')
    const parsedRetryAfter = retryAfterHeader ? parseInt(retryAfterHeader, 10) : undefined
    const retryAfter = Number.isFinite(parsedRetryAfter)
      ? parsedRetryAfter
      : (typeof error?.retry_after === 'number' ? error.retry_after : undefined)

    throw new ApiError(
      response.status,
      error?.detail ?? `Search failed (${response.status})`,
      retryAfter
    )
  }

  return response.json()
}
