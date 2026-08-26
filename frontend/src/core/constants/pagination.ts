/**
 * Pagination and Sorting Constants
 * Standardized pagination defaults and sort order definitions
 * 
 * @module core/constants/pagination
 */

/**
 * Default pagination configuration
 */
export const PAGINATION_DEFAULTS = {
  /** Default page size */
  DEFAULT_PAGE_SIZE: 20,
  /** Minimum page size */
  MIN_PAGE_SIZE: 5,
  /** Maximum page size */
  MAX_PAGE_SIZE: 100,
  /** Default page number (1-indexed) */
  DEFAULT_PAGE: 1,
  /** Common page size options */
  PAGE_SIZE_OPTIONS: [5, 10, 20, 50, 100],
} as const;

/**
 * Sort order directions
 */
export const SORT_ORDERS = {
  ASCENDING: 'asc',
  DESCENDING: 'desc',
} as const;

/**
 * Sort direction type
 */
export type SortOrder = typeof SORT_ORDERS[keyof typeof SORT_ORDERS];

/**
 * Toggle sort direction
 */
export function toggleSortOrder(current: SortOrder): SortOrder {
  return current === SORT_ORDERS.ASCENDING
    ? SORT_ORDERS.DESCENDING
    : SORT_ORDERS.ASCENDING;
}

/**
 * Calculate total pages
 */
export function calculateTotalPages(totalItems: number, pageSize: number): number {
  if (pageSize <= 0) return 0;
  return Math.ceil(totalItems / pageSize);
}

/**
 * Calculate item range for current page
 */
export function calculateItemRange(
  page: number,
  pageSize: number,
  totalItems: number
): { start: number; end: number } {
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalItems);
  return { start, end };
}

/**
 * Validate page number
 */
export function validatePage(page: number, totalPages: number): number {
  if (isNaN(page) || page < 1) return 1;
  if (page > totalPages) return Math.max(1, totalPages);
  return page;
}

/**
 * Validate page size
 */
export function validatePageSize(pageSize: number): number {
  const { MIN_PAGE_SIZE, MAX_PAGE_SIZE, DEFAULT_PAGE_SIZE } = PAGINATION_DEFAULTS;
  if (isNaN(pageSize) || pageSize < MIN_PAGE_SIZE) return DEFAULT_PAGE_SIZE;
  if (pageSize > MAX_PAGE_SIZE) return MAX_PAGE_SIZE;
  return pageSize;
}

/**
 * Generate page range for pagination control
 */
export function generatePageRange(
  currentPage: number,
  totalPages: number,
  maxVisible: number = 7
): (number | 'ellipsis')[] {
  const pages: (number | 'ellipsis')[] = [];
  
  if (totalPages <= maxVisible) {
    // Show all pages
    for (let i = 1; i <= totalPages; i++) {
      pages.push(i);
    }
  } else {
    // Always show first page
    pages.push(1);
    
    // Calculate visible range around current page
    const halfVisible = Math.floor((maxVisible - 2) / 2);
    let start = Math.max(2, currentPage - halfVisible);
    let end = Math.min(totalPages - 1, currentPage + halfVisible);
    
    // Adjust range if at boundaries
    if (currentPage <= halfVisible + 1) {
      end = Math.min(totalPages - 1, maxVisible - 1);
    } else if (currentPage >= totalPages - halfVisible) {
      start = Math.max(2, totalPages - maxVisible + 2);
    }
    
    // Add ellipsis after first page if needed
    if (start > 2) {
      pages.push('ellipsis');
    }
    
    // Add visible pages
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    // Add ellipsis before last page if needed
    if (end < totalPages - 1) {
      pages.push('ellipsis');
    }
    
    // Always show last page
    pages.push(totalPages);
  }
  
  return pages;
}
