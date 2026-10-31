import { Search } from "lucide-react";
import { useCallback, useRef } from "react";

/** @typedef {Object} SearchInputProps
 * @property {string} value
 * @property {(value: string) => void} onChange
 * @property {string} [placeholder]
 * @property {number} [debounceMs]
 */

/** Controlled search input with optional debouncing. */
export function SearchInput({ value, onChange, placeholder = "Search…", debounceMs = 300 }) {
  const inputRef = useRef(null);
  const timerRef = useRef(null);

  const handleChange = useCallback(
    (e) => {
      const val = e.target.value;
      onChange(val);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        onChange(val);
      }, debounceMs);
    },
    [onChange, debounceMs]
  );

  return (
    <div className="search-input">
      <input
        ref={inputRef}
        className="input search-input__field"
        type="search"
        placeholder={placeholder}
        value={value}
        onChange={handleChange}
        aria-label="Search"
      />
      <Search className="search-input__icon" aria-hidden="true" />
    </div>
  );
}

SearchInput.displayName = "SearchInput";
