import type { SearchResult } from '../types/search'
import { escapeRegExp } from '../lib/query'

export function Highlight({ text, terms }: { text: string; terms: string[] }) {
  if (terms.length === 0) return <>{text}</>
  const pattern = new RegExp(`(${terms.map(escapeRegExp).join('|')})`, 'gi')
  return (
    <>
      {text.split(pattern).map((part, i) => (i % 2 === 1 ? <mark key={i}>{part}</mark> : part))}
    </>
  )
}

export type SearchResultItemProps = {
  result: SearchResult
  terms: string[]
}

function parseUrl(raw: string) {
  try {
    const u = new URL(raw)
    const segments = u.pathname.split('/').filter(Boolean)
    const bareHost = u.hostname.replace(/^www\./, '')
    const label = bareHost.split('.').slice(-2, -1)[0] ?? bareHost
    return {
      origin: u.origin,
      hostname: u.hostname,
      crumbs: segments.length ? ' › ' + segments.join(' › ') : '',
      siteName: label.charAt(0).toUpperCase() + label.slice(1),
    }
  } catch {
    return { origin: raw, hostname: '', crumbs: '', siteName: raw }
  }
}

export function SearchResultItem({ result, terms }: SearchResultItemProps) {
  const { origin, hostname, crumbs, siteName } = parseUrl(result.url)
  const favicon = `https://www.google.com/s2/favicons?domain=${hostname}&sz=64`

  return (
    <li className="result">
      <div className="result-header">
        <span className="result-favicon">
          <img
            src={favicon}
            alt=""
            width={25}
            height={25}
            onError={(e) => (e.currentTarget.style.visibility = 'hidden')}
          />
        </span>
        <div className="result-site">
          <span className="site-name">{siteName}</span>
          <cite className="site-url">
            {origin}
            <span className="crumbs">{crumbs}</span>
          </cite>
        </div>
      </div>

      <h2 className="result-title">
        <a href={result.url} target="_blank" rel="noopener noreferrer">
          <Highlight text={result.title} terms={terms} />
        </a>
      </h2>

      <p className="result-snippet">
        <Highlight text={result.snippet} terms={terms} />
      </p>
    </li>
  )
}

export default SearchResultItem