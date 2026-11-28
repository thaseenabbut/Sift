import { useEffect, useId, useRef, useState } from 'react'
import type { MouseEvent } from 'react'
import '../styles/AIOverview.css'
import ReactMarkdown from 'react-markdown'
import type { AIOverviewResponse, OverviewSource } from '../types/ai-overview'
import { ApiError, getAIOverview } from '../lib/api'

type OverviewState =
  | { status: 'loading' }
  | { status: 'success'; data: AIOverviewResponse }
  | { status: 'error'; message: string }
  | { status: 'hidden' }

const OVERVIEW_MESSAGES = {
  NOT_GENERATED_DUE_TO_INSUFFICIENT_EVIDENCE:
    'There isn’t enough relevant information to generate an AI Overview.',
  NOT_GENERATED_DUE_TO_LLM_ERROR:
    'AI Overview is temporarily unavailable. Please try again later.',
  NOT_GENERATED_DUE_TO_EMPTY_QUERY:
    'Please enter a search query to generate an AI Overview.',
  NOT_GENERATED_DUE_TO_RETRIEVAL_ERROR:
    'We couldn’t retrieve information for the AI Overview. Please try again later.',
}

/* ------------------------------------------------------------------ */
/* Data fetching                                                       */
/* ------------------------------------------------------------------ */

const REQUEST_TIMEOUT_MS = 15_000

function useAiOverview(query: string): OverviewState {
  const [prevQuery, setPrevQuery] = useState(query)
  const [state, setState] = useState<OverviewState>({ status: 'loading' })

  if (query !== prevQuery) {
    setPrevQuery(query)
    setState({ status: 'loading' })
  }

  useEffect(() => {
    const controller = new AbortController()
    let timedOut = false

    const timer = setTimeout(() => {
      timedOut = true
      controller.abort()
    }, REQUEST_TIMEOUT_MS)

    getAIOverview(query, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return

        if (data.status === 'GENERATED_SUCCESSFULLY' && data.overview) {
          setState({ status: 'success', data })
          return
        }

        setState({
          status: 'error',
          message:
            OVERVIEW_MESSAGES[data.status as keyof typeof OVERVIEW_MESSAGES] ??
            'AI Overview is temporarily unavailable. Please try again later.',
        })
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted && !timedOut) return

        let message = 'AI Overview is temporarily unavailable. Please try again later.'

        if (timedOut) {
          message = 'AI Overview is taking longer than expected. Please try again later.'
        } else if (err instanceof ApiError) {
          if (err.status === 429) {
            message = 'AI Overview is temporarily busy. Please try again in a moment.'
          } else if (err.status === 401 || err.status === 403) {
            message = 'AI Overview is currently unavailable. You can still explore your search results below.'
          }
        }

        setState({ status: 'error', message })
      })
      .finally(() => clearTimeout(timer))

    return () => {
      controller.abort()
      clearTimeout(timer)
    }
  }, [query])

  return state
}

/* ------------------------------------------------------------------ */
/* Sources pill and dialog                                             */
/* ------------------------------------------------------------------ */

function hostOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return ''
  }
}

// Favicons come from Google's favicon service. To avoid a third party, have
// your backend return a favicon URL for each source, or change this function.
function faviconUrl(host: string): string {
  return `https://www.google.com/s2/favicons?domain=${encodeURIComponent(host)}&sz=64`
}

// A site's icon, or its first letter if the icon can't load.
function Favicon({ host }: { host: string }) {
  const [failed, setFailed] = useState(false)

  if (failed || !host) {
    return (
      <span className="favicon favicon-fallback" aria-hidden="true">
        {host.charAt(0).toUpperCase()}
      </span>
    )
  }
  return (
    <img
      className="favicon"
      src={faviconUrl(host)}
      alt=""
      loading="lazy"
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
    />
  )
}

function Sources({ sources }: { sources: OverviewSource[] }) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  const [expanded, setExpanded] = useState(false)

  // The pill shows the icons of up to three different sites.
  const hosts = [...new Set(sources.map((source) => hostOf(source.url)).filter(Boolean))].slice(0, 3)

  // A modal <dialog> gives us the dimmed backdrop, Escape to close, focus
  // trapping, and focus returning to the pill, all built in.
  const openDialog = () => {
    dialogRef.current?.showModal()
    setExpanded(true)
  }
  const closeDialog = () => dialogRef.current?.close()

  // A click on the dimmed backdrop reports the <dialog> itself as the target;
  // a click on anything inside reports that inner element.
  const handleDialogClick = (event: MouseEvent<HTMLDialogElement>) => {
    if (event.target === event.currentTarget) closeDialog()
  }

  return (
    <>
      <button
        type="button"
        className="sources-pill"
        aria-haspopup="dialog"
        aria-expanded={expanded}
        onClick={openDialog}
      >
        <span className="favicon-stack" aria-hidden="true">
          {hosts.map((host) => (
            <Favicon key={host} host={host} />
          ))}
        </span>
        Sources
      </button>

      <dialog
        ref={dialogRef}
        className="sources-dialog"
        aria-labelledby={titleId}
        onClick={handleDialogClick}
        onClose={() => setExpanded(false)}
      >
        <div className="sources-header">
          <h3 id={titleId} className="sources-title">
            Sources
          </h3>
          <button
            type="button"
            className="sources-close"
            onClick={closeDialog}
            aria-label="Close sources"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
              <path
                d="m6 6 12 12M18 6 6 18"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                fill="none"
              />
            </svg>
          </button>
        </div>

        <ul className="sources-list">
          {sources.map((source, index) => (
            <li key={`${source.url}-${index}`}>
              <a href={source.url} target="_blank" rel="noopener noreferrer">
                <Favicon host={hostOf(source.url)} />
                <span className="sources-text">
                  <span className="sources-name">{source.title}</span>
                  <span className="sources-host">{hostOf(source.url)}</span>
                </span>
              </a>
            </li>
          ))}
        </ul>
      </dialog>
    </>
  )
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

/**
 * Render with a `key` that changes on every search, so each search starts
 * fresh in the loading state:  <AiOverview key={searchKey} query={submitted} />
 */
export function AiOverview({ query }: { query: string }) {
  const headingId = useId()
  const state = useAiOverview(query)

  // Free tier limit reached: no heading, no message, nothing.
  if (state.status === 'hidden') return null

  return (
    <section className="ai-overview" aria-labelledby={headingId}>
      <h2 id={headingId} className="ai-overview-heading">
        Sift AI Overview
      </h2>

      <div className="ai-overview-body" aria-live="polite">
        {state.status === 'loading' && (
          <>
            <span className="visually-hidden">Generating overview…</span>
            <div className="ai-overview-skeleton" aria-hidden="true">
              <span />
              <span />
              <span />
              <span />
            </div>
          </>
        )}

        {state.status === 'success' && (
          <div className="ai-overview-markdown">
            <ReactMarkdown>{state.data.overview ?? ''}</ReactMarkdown>
          </div>
        )}

        {state.status === 'error' && <p className="ai-overview-error">{state.message}</p>}
      </div>

      {state.status === 'success' && (
        <>
          {state.data.sources.length > 0 && (
            <Sources sources={state.data.sources} />
          )}
          <p className="ai-overview-disclaimer">
            AI can make mistakes. Please verify important info.
          </p>
        </>
      )}
    </section>
  )
}

export default AiOverview