import '../styles/Pagination.css'

export type PaginationProps = {
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}

type PageItem = number | 'gap'

// Which page numbers to show: always first, last, and current ± 1.
// Anything skipped in between becomes a "…" (gap).
function getPageItems(page: number, totalPages: number, siblings = 1): PageItem[] {
  const wanted = new Set<number>([1, totalPages])
  for (let p = page - siblings; p <= page + siblings; p++) {
    if (p >= 1 && p <= totalPages) wanted.add(p)
  }

  const sorted = [...wanted].sort((a, b) => a - b)
  const items: PageItem[] = []
  sorted.forEach((p, i) => {
    if (i > 0 && p - sorted[i - 1] > 1) items.push('gap')
    items.push(p)
  })
  return items
}

export function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null

  return (
    <nav className="pagination" aria-label="Pagination">
      <button
        type="button"
        className="page-button"
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
      >
        Previous
      </button>

      {getPageItems(page, totalPages).map((item, i) =>
        item === 'gap' ? (
          <span key={`gap-${i}`} className="page-gap" aria-hidden="true">
            …
          </span>
        ) : (
          <button
            key={item}
            type="button"
            className="page-button"
            aria-current={item === page ? 'page' : undefined}
            aria-label={`Page ${item}`}
            onClick={() => onPageChange(item)}
          >
            {item}
          </button>
        )
      )}

      <button
        type="button"
        className="page-button"
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
      >
        Next
      </button>
    </nav>
  )
}

export default Pagination