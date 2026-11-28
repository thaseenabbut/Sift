import { useMemo, useState } from 'react'
import type { SearchResponse, Status } from '../types/search'
import { SearchResultItem } from './SearchResultItem'
import { getHighlightTerms, parseQuery } from '../lib/query'
import { Pagination } from './Pagination'
import { AiOverview } from './AIOverview'
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
  error,
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

  const [prevSubmitted, setPrevSubmitted] = useState(submitted)
  const [overviewActivated, setOverviewActivated] = useState(page === 1)

  if (submitted !== prevSubmitted) {
    setPrevSubmitted(submitted)
    setOverviewActivated(page === 1)
  } else if (page === 1 && !overviewActivated) {
    setOverviewActivated(true)
  }

  if (status === 'idle') {
    return null
  }

  const results = response?.results ?? []
  const totalResults = response?.total ?? results.length
  const timeTaken = response?.time_taken
  const showOverview =
    overviewActivated && (status === 'loading' || (status === 'done' && results.length > 0))

  return (
    <main className="results" aria-busy={status === 'loading'}>
      {showOverview && (
        <div hidden={page > 1}>
          <AiOverview key={submitted} query={submitted} />
        </div>
      )}

      {status === 'loading' && <SkeletonList />}

      {status === 'error' && (
        <section className="notice" role="alert">
          <h2>Search error</h2>
          <p>{error || 'Something went wrong. Please try again.'}</p>
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
            About {totalResults.toLocaleString()} {totalResults === 1 ? 'result' : 'results'}
            {typeof timeTaken === 'number' && ` (${timeTaken.toFixed(2)} seconds)`} for “{submitted}”
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