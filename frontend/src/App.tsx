import { useCallback, useMemo, useRef, useEffect, useState } from 'react'
import './App.css'
import type { SearchResponse, Status } from './types/search'
import { searchSift } from './lib/api'
import { getHighlightTerms, parseQuery } from './lib/query'
import { SearchBar } from './components/SearchBar'
import { SearchResults } from './components/SearchResults'

const PAGE_SIZE = 10

function App() {
  const [query, setQuery] = useState('') // what is in the input right now
  const [submitted, setSubmitted] = useState('') // the query the current results belong to
  const [status, setStatus] = useState<Status>('idle')
  const [response, setResponse] = useState<SearchResponse | null>(null)
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')

  const inputRef = useRef<HTMLInputElement>(null)
  // Every search gets an id. If a slower, older request finishes after a newer
  // one, its id no longer matches and we ignore it (a classic race condition).
  const requestId = useRef(0)

  useEffect(() => {
    if (submitted.trim() === '') {
      document.title = 'Sift Search'
    } else {
      document.title = `${submitted} - Sift Search`
    }
  }, [submitted]) // Triggers whenever a search completes/submits or resets

  const runSearch = useCallback(async (raw: string, targetPage = 1) => {
    const trimmed = raw.trim()
    if (!trimmed) return

    const id = ++requestId.current
    setQuery(trimmed)
    setSubmitted(trimmed)
    setPage(targetPage)
    setStatus('loading')
    setError('')

    try {
      const data = await searchSift(trimmed, targetPage)
      if (id !== requestId.current) return
      setResponse(data)
      setStatus('done')
    } catch (err) {
      if (id !== requestId.current) return
      setError(err instanceof Error ? err.message : 'Something went wrong.')
      setStatus('error')
    }
  }, [])

  const goHome = () => {
    requestId.current++
    setQuery('')
    setSubmitted('')
    setResponse(null)
    setStatus('idle')
    inputRef.current?.focus()
  }

  const highlightTerms = useMemo(() => getHighlightTerms(parseQuery(submitted)), [submitted])
  const totalPages = response ? Math.max(1, Math.ceil(response.total / PAGE_SIZE)) : 1

  const mode = status === 'idle' ? 'home' : 'results'

  return (
    <div className="sift">
      <header className="masthead" data-mode={mode}>
        <h1 className="wordmark">
          <button type="button" onClick={goHome} aria-label="Sift home">
            Sift
          </button>
        </h1>

        {mode === 'home' && <p className="tagline">An open-source search engine.</p>}

        <SearchBar
          value={query}
          inputRef={inputRef}
          onChange={setQuery}
          onSubmit={() => runSearch(query)}
        />
      </header>

      {mode === 'results' && (
        <SearchResults
          status={status}
          response={response}
          error={error}
          submitted={submitted}
          highlightTerms={highlightTerms}
          page={page}
          totalPages={totalPages}
          onPageChange={(p) => {
            runSearch(submitted, p)
            window.scrollTo({ top: 0, behavior: 'smooth' })
          }}
        />
      )}
    </div>
  )
}

export default App