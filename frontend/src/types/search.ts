export type SearchResult = {
  title: string
  url: string
  snippet: string
  score: number
}

export type SearchResponse = {
  query: string
  count: number
  total: number
  page: number
  page_size: number
  results: SearchResult[]
}

export type Status = 'idle' | 'loading' | 'done' | 'error'

export type ParsedQuery = {
  terms: string[]
  phrases: string[]
  excluded: string[]
  operators: Record<string, string>
}
