import { Children, forwardRef } from "react";

/** @typedef {Object} CardProps
 * @property {boolean} [padded]
 */

/** Surface container with optional header/body/footer sections. */
export const Card = forwardRef(
  /** @param {import("react").HTMLAttributes<HTMLDivElement> & CardProps} props */
  ({ className, padded = false, children, ...props }, ref) => (
    <div
      ref={ref}
      className={["card", padded ? "card--padded" : "", className]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {Children.toArray(children).map((child, i) => {
        if (!child) return null;
        const type = child.type.displayName ?? child.type.name ?? "";
        if (type === "CardHeader") return <div className="card__header">{child}</div>;
        if (type === "CardBody") return <div className="card__body">{child}</div>;
        if (type === "CardFooter") return <div className="card__footer">{child}</div>;
        return child;
      })}
    </div>
  )
);

Card.displayName = "Card";

/** @typedef {Object} CardHeaderProps */
/** @typedef {Object} CardBodyProps */
/** @typedef {Object} CardFooterProps */

export const CardHeader = forwardRef(
  /** @param {import("react").HTMLAttributes<HTMLDivElement> & CardHeaderProps} props */
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={["card__header", className].filter(Boolean).join(" ")} {...props}>
      {children}
    </div>
  )
);
CardHeader.displayName = "CardHeader";

export const CardBody = forwardRef(
  /** @param {import("react").HTMLAttributes<HTMLDivElement> & CardBodyProps} props */
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={["card__body", className].filter(Boolean).join(" ")} {...props}>
      {children}
    </div>
  )
);
CardBody.displayName = "CardBody";

export const CardFooter = forwardRef(
  /** @param {import("react").HTMLAttributes<HTMLDivElement> & CardFooterProps} props */
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={["card__footer", className].filter(Boolean).join(" ")} {...props}>
      {children}
    </div>
  )
);
CardFooter.displayName = "CardFooter";
