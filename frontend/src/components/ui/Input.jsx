import { forwardRef } from "react";

/** @typedef {Object} InputProps
 * @property {string} [label]
 * @property {string} [error]
 * @property {"sm"|"md"} [size]
 */

/** Labeled text input with error state. */
export const Input = forwardRef(
  /** @param {import("react").InputHTMLAttributes<HTMLInputElement> & InputProps} props */
  ({ className, label, error, size = "md", ...props }, ref) => (
    <div className={["field", error ? "field--error" : ""].filter(Boolean).join(" ")}>
      {label && <label className="field-label">{label}</label>}
      <input
        ref={ref}
        className={[
          "input",
          `input--${size}`,
          error ? "input--error" : "",
          className,
        ].filter(Boolean).join(" ")}
        {...props}
      />
      {error && <span className="field-error">{error}</span>}
    </div>
  )
);

Input.displayName = "Input";
