import type { SearchResult } from '../types/search'
import { escapeRegExp, splitUrl } from '../lib/query'

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

export function SearchResultItem({ result, terms }: SearchResultItemProps) {
  const { host, path } = splitUrl(result.url)
  return (
    <li className="result">
      <p className="result-url">
        <span className="host">{host}</span>
        <span className="path">{path}</span>
      </p>
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
