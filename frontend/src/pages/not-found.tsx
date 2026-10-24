import { Link } from 'react-router-dom'
import '../styles/not-found.css'

export function NotFound() {
  return (
    <div className="sift not-found-page">
      <div className="not-found-backdrop" aria-hidden="true" />

      <main className="not-found-content">
        <span className="not-found-code" aria-hidden="true">404</span>

        <h1 className="not-found-title">Page not found</h1>
        <p className="not-found-desc">
          The page you're looking for doesn't exist or may have been moved.
        </p>

        <Link to="/" className="primary-button not-found-home">
          Back to Sift
        </Link>
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

export default NotFound
