import { forwardRef } from "react";

/** @typedef {Object} ButtonProps
 * @property {"primary"|"ghost"|"danger"} [variant]
 * @property {"sm"|"md"|"lg"} [size]
 * @property {boolean} [fullWidth]
 * @property {boolean} [loading]
 */

/** Primary action button with loading state and variant styling. */
export const Button = forwardRef(
  /** @param {import("react").ButtonHTMLAttributes<HTMLButtonElement> & ButtonProps} props */
  ({ className, variant = "primary", size = "md", fullWidth, loading, children, disabled, ...props }, ref) => (
    <button
      ref={ref}
      className={[
        "btn",
        `btn--${variant}`,
        `btn--${size}`,
        fullWidth ? "btn--full" : "",
        className,
      ].filter(Boolean).join(" ")}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="currentColor"
          style={{ marginRight: "var(--erp-space-2)" }}
        >
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" strokeLinecap="round" />
        </svg>
      )}
      {children}
    </button>
  )
);

Button.displayName = "Button";
