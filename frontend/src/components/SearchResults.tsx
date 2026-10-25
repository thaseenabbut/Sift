import { useMemo } from 'react'
import type { SearchResponse, Status } from '../types/search'
import { SearchResultItem } from './SearchResultItem'
import { getHighlightTerms, parseQuery } from '../lib/query'
import { Pagination } from './Pagination'
import '../styles/SearchResults.css'

export type SearchResultsProps = {
  status: Status
  response: SearchResponse | null
  error?: string
  submitted: string
  highlightTerms?: string[]
  page?: number
  totalPages?: number
  onPageChange?: (page: number) => void
}

export function SkeletonList() {
  return (
    <ol className="result-list" aria-hidden="true">
      {[0, 1, 2].map((n) => (
        <li key={n} className="result skeleton">
          <span />
          <span />
          <span />
          <span />
        </li>
      ))}
    </ol>
  )
}

export function SearchResults({
  status,
  response,
  submitted,
  highlightTerms: propHighlightTerms,
  page = 1,
  totalPages = 1,
  onPageChange,
}: SearchResultsProps) {
  const computedHighlightTerms = useMemo(
    () => getHighlightTerms(parseQuery(submitted)),
    [submitted]
  )
  const terms = propHighlightTerms ?? computedHighlightTerms

  if (status === 'idle') {
    return null
  }

  const results = response?.results ?? []

  return (
    <main className="results" aria-busy={status === 'loading'}>
      {status === 'loading' && <SkeletonList />}

      {status === 'error' && (
        <section className="notice" role="alert">
          <h2>Can’t reach Sift right now</h2>
          <p>Please check your connection and try again.</p>
        </section>
      )}

      {status === 'done' && response && results.length === 0 && (
        <section className="notice">
          <h2>Your search <b>{submitted}</b> did not match any documents.</h2>
          <p>
            Check the spelling, use fewer words, or remove an exclusion like <code>-word</code>{' '}
            or a <code>site:</code> filter.
          </p>
        </section>
      )}

      {status === 'done' && response && results.length > 0 && (
        <>
          <p className="summary" aria-live="polite">
            {results.length} {results.length === 1 ? 'result' : 'results'} for “{submitted}”
          </p>
          <ol className="result-list">
            {results.map((result) => (
              <SearchResultItem
                key={result.url}
                result={result}
                terms={terms}
              />
            ))}
          </ol>
          {onPageChange && (
            <Pagination page={page} totalPages={totalPages} onPageChange={onPageChange} />
          )}
        </>
      )}
    </main>
  )
}

export default SearchResults