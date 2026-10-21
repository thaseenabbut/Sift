import type { FormEvent, RefObject } from 'react'
import '../styles/SearchBar.css'

export function SearchIcon() {
  return (
    <svg className="searchbar-icon" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M15.5 15.5 21 21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export type SearchBarProps = {
  value: string
  inputRef: RefObject<HTMLInputElement | null>
  onChange: (value: string) => void
  onSubmit: () => void
}

export function SearchBar({ value, inputRef, onChange, onSubmit }: SearchBarProps) {
  const handleSubmit = (event: FormEvent) => {
    event.preventDefault() // stop the browser from reloading the page
    onSubmit()
  }

  return (
    <form className="searchbar" role="search" onSubmit={handleSubmit}>
      <SearchIcon />
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search or enter website name"
        aria-label="Search Sift"
        autoComplete="off"
        autoCapitalize="off"
        spellCheck={false}
        enterKeyHint="search"
      />
    </form>
  )
}

export default SearchBar
