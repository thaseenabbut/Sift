import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import '../styles/too-many-requests.css'

type TooManyRequestsProps = {
  /** Seconds to wait before retrying (from the Retry-After header, if you have it). */
  retryAfter?: number
  onRetry?: () => void
}

export function TooManyRequests({
  retryAfter,
  onRetry = () => window.location.reload(),
}: TooManyRequestsProps) {
  const [secondsLeft, setSecondsLeft] = useState(retryAfter ?? 0)

  useEffect(() => {
    document.title = '429 Too Many Requests \u2013 Sift'
  }, [])

  // Count down once per second. Each tick changes secondsLeft, which re-runs
  // this effect and schedules the next tick; the cleanup cancels a pending one.
  useEffect(() => {
    if (secondsLeft <= 0) return
    const id = setTimeout(() => setSecondsLeft((s) => s - 1), 1000)
    return () => clearTimeout(id)
  }, [secondsLeft])

  const waiting = secondsLeft > 0

  return (
    <div className="sift too-many-requests-page">
      <div className="too-many-requests-backdrop" aria-hidden="true" />

      <main className="too-many-requests-content">
        <span className="too-many-requests-code" aria-hidden="true">429</span>

        <h1 className="too-many-requests-title">Too many requests</h1>
        <p className="too-many-requests-desc">
          You’ve sent a lot of searches in a short time. Wait a moment, then try again.
        </p>

        <button
          type="button"
          className="primary-button too-many-requests-retry"
          onClick={onRetry}
          disabled={waiting}
        >
          {waiting ? `Try again in ${secondsLeft}s` : 'Try again'}
        </button>
      </main>

      <footer className="site-footer">
        <nav className="footer-links" aria-label="Footer">
          <Link to="/about">About</Link>
          <span>·</span>
          <Link to="/privacy">Privacy</Link>
          <span>·</span>
          <Link to="/terms">Terms</Link>
        </nav>
      </footer>
    </div>
  )
}

export default TooManyRequests