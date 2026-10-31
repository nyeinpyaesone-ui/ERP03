import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "./Button";

/** @typedef {Object} PaginationProps
 * @property {number} page
 * @property {number} pageSize
 * @property {number} total
 * @property {(page: number) => void} onPageChange
 */

/** Paginated navigation with prev/next and page info. */
export function Pagination({ page, pageSize, total, onPageChange }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const goTo = (p) => {
    const clamped = Math.max(1, Math.min(totalPages, p));
    if (clamped !== page) onPageChange(clamped);
  };

  return (
    <nav className="pagination" aria-label="Pagination">
      <div className="pagination__info">
        Showing <b>{((page - 1) * pageSize) + 1}</b>{" "}
        to <b>{Math.min(page * pageSize, total)}</b> of <b>{total}</b>
      </div>
      <div className="pagination__controls">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => goTo(page - 1)}
          disabled={page === 1}
          aria-label="Previous page"
        >
          <ChevronLeft size={16} />
        </Button>
        <span className="pagination__page">
          {page} / {totalPages}
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => goTo(page + 1)}
          disabled={page === totalPages}
          aria-label="Next page"
        >
          <ChevronRight size={16} />
        </Button>
      </div>
    </nav>
  );
}

Pagination.displayName = "Pagination";
