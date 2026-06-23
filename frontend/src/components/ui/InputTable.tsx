import React from 'react';

// ─── Types ────────────────────────────────────────────────────────────────────

export type TableColumn = {
  key: string
  label: string
  filterable?: boolean
  children?: TableColumn[]
}

type TableProps = {
  columns: TableColumn[]
  rowCount?: number
}

// ─── Sub-components ───────────────────────────────────────────────────────────

type ThCellProps = {
  label: string
  filterable?: boolean
}

function ThCell({ label, filterable }: ThCellProps) {
  if (!filterable) return <>{label}</>

  return (
    <div className="flex items-center justify-center gap-1">
      {label}
      <button
        type="button"
        aria-label={`Filter ${label}`}
        className="text-text-inverse/70 hover:text-text-inverse"
      >
        <svg
            viewBox="0 0 24 24"
            className="h-3.5 w-3.5 text-brand-primary"
            fill="none"
            stroke="white"
            strokeWidth="2"
        >
            <path d="M4 5h16l-6 7v6l-4 2v-8L4 5z" />
        </svg>
      </button>
    </div>
  )
}

// ─── Component ────────────────────────────────────────────────────────────────

export function InputTable({ columns, rowCount = 10 }: TableProps) {
  const childColumns = columns.flatMap((col) => col.children ?? [])
  const hasSubHeaders = childColumns.length > 0
  const totalLeafColumns = columns.reduce(
    (sum, col) => sum + (col.children ? col.children.length : 1),
    0,
    )

  return (
    <div className="overflow-x-auto rounded-lg border border-border-default">
      <table className="w-full text-xs [border-spacing:0]"> {/* Added border-spacing:0 to remove gaps */}

        {/* ───────── HEADER ───────── */}
        <thead>

          {/* TOP HEADER */}
          <tr className="text-text-inverse">
            {columns.map((col) => ( // Removed idx as it's no longer needed for conditional border-l
              <th
                key={col.key}
                rowSpan={col.children ? 1 : hasSubHeaders ? 2 : 1}
                colSpan={col.children ? col.children.length : 1}
                className={`
                  px-3 py-2.5 text-center font-semibold
                  bg-[linear-gradient(180deg,#17479E_0%,#0D2D6B_100%)]
                  border border-white/80 // Applied all borders explicitly
                  ${col.children ? 'border-b border-white/80' : ''} // Ensure bottom border for top-level headers with children
                `}
              >
                <ThCell label={col.label} filterable={col.filterable} />
              </th>
            ))}
          </tr>

          {/* SUB HEADER */}
          {hasSubHeaders && (
            <tr className="text-text-inverse">
              {childColumns.map((child) => ( // Removed idx
                <th
                  key={child.key}
                  className={`
                    px-3 py-2.5 text-center font-semibold
                    bg-[linear-gradient(180deg,#17479E_0%,#0D2D6B_100%)]
                    border border-white/80 // Applied all borders explicitly
                  `}
                >
                  <ThCell label={child.label} filterable={child.filterable} />
                </th>
              ))}
            </tr>
          )}

        </thead>

        {/* ───────── BODY ───────── */}
        <tbody>
          {Array.from({ length: rowCount }, (_, rowIdx) => (
            <tr key={rowIdx} className="bg-surface-card">

              {/* SR NO */}
              <td className="
                border border-border-default // Applied all borders explicitly
                px-3 py-3 text-center text-text-secondary font-medium
              ">
                {String(rowIdx + 1).padStart(2, '0')}
              </td>

              {/* DATA CELLS */}
              {Array.from({ length: totalLeafColumns - 1 }, (_, cellIdx) => (
                <td
                  key={cellIdx}
                  className="
                    border border-border-default // Applied all borders explicitly
                    px-3 py-3 text-center text-text-primary
                  "
                />
              ))}

            </tr>
          ))}
        </tbody>

      </table>
    </div>
  )
}