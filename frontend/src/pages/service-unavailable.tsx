import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import '../styles/service-unavailable.css'

type ServiceUnavailableProps = {
  onRetry?: () => void
  homeHref?: string
  onHome?: () => void
}

export function ServiceUnavailable({
  onRetry = () => window.location.reload(),
  homeHref,
  onHome,
}: ServiceUnavailableProps) {
  useEffect(() => {
    document.title = '503 Service Unavailable \u2013 Sift'
  }, [])

  return (
    <div className="sift service-unavailable-page">
      <div className="service-unavailable-backdrop" aria-hidden="true" />

      <main className="service-unavailable-content">
        <span className="service-unavailable-code" aria-hidden="true">503</span>

        <h1 className="service-unavailable-title">Service unavailable</h1>
        <p className="service-unavailable-desc">
          Sift can’t handle your request right now. This is usually temporary so please try again later
        </p>

        <div className="service-unavailable-actions">
          <button style={{ color: '#1c1c1b', fontWeight: '650' }} type="button" className="primary-button service-unavailable-retry" onClick={onRetry}>
            Try again
          </button>
          {homeHref && (
            <Link to={homeHref} className="service-unavailable-home" onClick={onHome}>
              Back to Sift
            </Link>
          )}
        </div>
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

export default ServiceUnavailable
