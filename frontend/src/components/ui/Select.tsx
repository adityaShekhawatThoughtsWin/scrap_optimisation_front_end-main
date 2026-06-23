import KeyboardArrowDownOutlinedIcon from '@mui/icons-material/KeyboardArrowDownOutlined'
import { useEffect, useId, useRef, useState } from 'react'

export type SelectOption<T extends string> = {
  value: T
  label: string
}

type SelectProps<T extends string> = {
  label: string
  placeholder: string
  options: SelectOption<T>[]
  value: T | null
  onChange: (value: T) => void
  disabled?: boolean
  active?: boolean
}

export function Select<T extends string>({
  label,
  placeholder,
  options,
  value,
  onChange,
  disabled = false,
  active = false,
}: SelectProps<T>) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const listboxId = useId()

  const selected = options.find((option) => option.value === value)

  useEffect(() => {
    if (!open) return

    const handlePointerDown = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handlePointerDown)
    return () => document.removeEventListener('mousedown', handlePointerDown)
  }, [open])

  return (
    <div ref={containerRef} className="relative flex w-full flex-col gap-3.5">
      <span className="text-xs font-medium text-text-label">{label}</span>

      <button
        type="button"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        onClick={() => !disabled && setOpen((prev) => !prev)}
        className={[
          'flex h-[42px] w-full items-center justify-between rounded-[10px] border bg-surface-card px-3.5 text-xs',
          'transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-accent',
          active && value
            ? 'border-text-dropdown text-text-dropdown'
            : 'border-border-default text-text-label',
          disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        <span className={selected ? 'text-text-dropdown' : ''}>
          {selected?.label ?? placeholder}
        </span>
        <KeyboardArrowDownOutlinedIcon
          className={['size-3.5 transition-transform', open ? 'rotate-180' : '']
            .filter(Boolean)
            .join(' ')}
        />
      </button>

      {open && !disabled && (
        <ul
          id={listboxId}
          role="listbox"
          className="absolute top-[calc(100%+4px)] z-20 max-h-48 w-full overflow-auto rounded-[10px] border border-border-dropdown bg-surface-card py-0"
          style={{ boxShadow: 'var(--shadow-dropdown)' }}
        >
          {options.map((option) => (
            <li key={option.value} role="option" aria-selected={value === option.value}>
              <button
                type="button"
                className="flex h-10 w-full items-center border-b border-border-dropdown px-5 text-left text-sm font-medium text-text-option last:border-b-0 hover:bg-surface-page"
                onClick={() => {
                  onChange(option.value)
                  setOpen(false)
                }}
              >
                {option.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
