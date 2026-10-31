import { forwardRef } from "react";

/** @typedef {"success"|"warning"|"danger"|"info"|"neutral"} BadgeVariant */

/** @typedef {Object} BadgeProps
 * @property {BadgeVariant} [variant]
 */

/** Status badge with semantic color variants. */
export const Badge = forwardRef(
  /** @param {import("react").HTMLAttributes<HTMLSpanElement> & BadgeProps} props */
  ({ className, variant = "neutral", children, ...props }, ref) => (
    <span
      ref={ref}
      className={[
        "badge",
        `badge--${variant}`,
        className,
      ].filter(Boolean).join(" ")}
      {...props}
    >
      {children}
    </span>
  )
);

Badge.displayName = "Badge";
