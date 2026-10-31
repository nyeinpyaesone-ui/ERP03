import { forwardRef } from "react";

/** @typedef {Object} TableProps */

/** Table with responsive horizontal scroll wrapper. */
export const Table = forwardRef(
  /** @param {import("react").HTMLAttributes<HTMLTableElement> & TableProps} props */
  ({ className, children, ...props }, ref) => (
    <div className="table-wrapper">
      <table
        ref={ref}
        className={["table", className].filter(Boolean).join(" ")}
        {...props}
      >
        {children}
      </table>
    </div>
  )
);

Table.displayName = "Table";

/** @typedef {Object} THeadProps */
export const THead = forwardRef(
  /** @param {import("react").HTMLAttributes<HTMLTableSectionElement> & THeadProps} props */
  ({ className, children, ...props }, ref) => (
    <thead ref={ref} className={className} {...props}>
      {children}
    </thead>
  )
);
THead.displayName = "THead";

/** @typedef {Object} TBodyProps */
export const TBody = forwardRef(
  /** @param {import("react").HTMLAttributes<HTMLTableSectionElement> & TBodyProps} props */
  ({ className, children, ...props }, ref) => (
    <tbody ref={ref} className={className} {...props}>
      {children}
    </tbody>
  )
);
TBody.displayName = "TBody";

/** @typedef {Object} TRProps */
export const TR = forwardRef(
  /** @param {import("react").HTMLAttributes<HTMLTableRowElement> & TRProps} props */
  ({ className, children, ...props }, ref) => (
    <tr ref={ref} className={className} {...props}>
      {children}
    </tr>
  )
);
TR.displayName = "TR";

/** @typedef {Object} THProps
 * @property {boolean} [sortable]
 */
export const TH = forwardRef(
  /** @param {import("react").HTMLAttributes<HTMLTableCellElement> & THProps} props */
  ({ className, sortable, children, ...props }, ref) => (
    <th
      ref={ref}
      className={["th", sortable ? "th--sortable" : "", className]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </th>
  )
);
TH.displayName = "TH";

/** @typedef {Object} TDProps */
export const TD = forwardRef(
  /** @param {import("react").HTMLAttributes<HTMLTableCellElement> & TDProps} props */
  ({ className, children, ...props }, ref) => (
    <td ref={ref} className={["td", className].filter(Boolean).join(" ")} {...props}>
      {children}
    </td>
  )
);
TD.displayName = "TD";
