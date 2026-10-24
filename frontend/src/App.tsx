import { useCallback, useMemo, useRef, useEffect, useState } from 'react'
import { Link, useSearchParams, useNavigate, useLocation } from 'react-router-dom'
import './App.css'
import type { SearchResponse, Status } from './types/search'
import { searchSift } from './lib/api'
import { getHighlightTerms, parseQuery } from './lib/query'
import { SearchBar } from './components/SearchBar'
import { SearchResults } from './components/SearchResults'

const PAGE_SIZE = 10

function App() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const location = useLocation()

  // URL is the source of truth for the submitted query and page.
  const urlQuery = searchParams.get('q') ?? ''
  const urlPage = Math.max(1, Number(searchParams.get('page') ?? '1'))

  const [query, setQuery] = useState(urlQuery) // what is in the input right now
  const [status, setStatus] = useState<Status>(urlQuery ? 'loading' : 'idle')
  const [response, setResponse] = useState<SearchResponse | null>(null)
  const [error, setError] = useState('')

  const inputRef = useRef<HTMLInputElement>(null)
  const requestId = useRef(0)

  useEffect(() => {
    setQuery(urlQuery)
  }, [urlQuery])

  useEffect(() => {
    if (urlQuery.trim() === '') {
      document.title = 'Sift Search'
    } else {
      document.title = `${urlQuery} - Sift Search`
    }
  }, [urlQuery])

  useEffect(() => {
    const trimmed = urlQuery.trim()
    if (!trimmed) {
      setStatus('idle')
      setResponse(null)
      setError('')
      return
    }

    const id = ++requestId.current
    setStatus('loading')
    setError('')

    searchSift(trimmed, urlPage)
      .then((data) => {
        if (id !== requestId.current) return
        setResponse(data)
        setStatus('done')
      })
      .catch((err) => {
        if (id !== requestId.current) return
        setError(err instanceof Error ? err.message : 'Something went wrong.')
        setStatus('error')
      })
  }, [urlQuery, urlPage])

  const handleSearch = useCallback((raw: string) => {
    const trimmed = raw.trim()
    if (!trimmed) return
    navigate(`/search?q=${encodeURIComponent(trimmed)}`)
  }, [navigate])

  const handlePageChange = useCallback((p: number) => {
    const params = new URLSearchParams({ q: urlQuery })
    if (p > 1) params.set('page', String(p))
    navigate(`/search?${params.toString()}`)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [navigate, urlQuery])

  const goHome = () => {
    requestId.current++
    navigate('/')
    inputRef.current?.focus()
  }

  const highlightTerms = useMemo(() => getHighlightTerms(parseQuery(urlQuery)), [urlQuery])
  const totalPages = response ? Math.max(1, Math.ceil(response.total / PAGE_SIZE)) : 1

  const mode = location.pathname === '/search' && urlQuery ? 'results' : 'home'

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
          onSubmit={() => handleSearch(query)}
        />
      </header>

      {mode === 'results' && (
        <SearchResults
          status={status}
          response={response}
          error={error}
          submitted={urlQuery}
          highlightTerms={highlightTerms}
          page={urlPage}
          totalPages={totalPages}
          onPageChange={handlePageChange}
        />
      )}

      {mode === 'home' && (
        <footer className="site-footer">
          <nav className="footer-links" aria-label="Footer">
            <Link to="/about">About</Link>
            <span>·</span>
            <Link to="/privacy">Privacy</Link>
            <span>·</span>
            <Link to="/terms">Terms</Link>
          </nav>
        </footer>
      )}
    </div>
  )
}

export default App