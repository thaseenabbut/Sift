import type { ParsedQuery } from '../types/search'

export const KNOWN_OPERATORS = new Set(['site', 'intitle', 'inurl', 'related'])

export function parseQuery(raw: string): ParsedQuery {
  const parsed: ParsedQuery = { terms: [], phrases: [], excluded: [], operators: {} }
  const tokenPattern = /(-?)(?:(\w+):)?(?:"([^"]+)"|(\S+))/g

  for (const match of raw.matchAll(tokenPattern)) {
    const [, minus, prefix, phrase, word] = match
    let value = (phrase ?? word).toLowerCase()

    // Skip half-typed tokens such as "site:" or a lone "-".
    if (value === '-' || value.endsWith(':')) continue

    const isOperator = Boolean(prefix) && KNOWN_OPERATORS.has(prefix.toLowerCase())

    if (isOperator) {
      parsed.operators[prefix.toLowerCase()] = value
    } else {
      // An unknown prefix like "http:" is just part of the word.
      if (prefix) value = `${prefix.toLowerCase()}:${value}`
      if (minus) parsed.excluded.push(value)
      else if (phrase) parsed.phrases.push(value)
      else parsed.terms.push(value)
    }
  }
  return parsed
}

export function getHighlightTerms(parsed: ParsedQuery): string[] {
  const all = [...parsed.phrases, ...parsed.terms, parsed.operators.intitle ?? '']
  return [...new Set(all.filter((t) => t.length > 1))].sort((a, b) => b.length - a.length)
}

export function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

export function splitUrl(url: string): { host: string; path: string } {
  try {
    const u = new URL(url)
    return { host: u.hostname.replace(/^www\./, ''), path: u.pathname === '/' ? '' : u.pathname }
  } catch {
    return { host: url, path: '' }
  }
}
