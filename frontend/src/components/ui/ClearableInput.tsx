import CloseIcon from '@mui/icons-material/Close'
import type { InputHTMLAttributes } from 'react'

type ClearableInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange'> & {
  value: string
  onChange: (value: string) => void
}

export function ClearableInput({ value, onChange, className = '', ...props }: ClearableInputProps) {
  return (
    <div className="relative flex items-center">
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={[
          'h-9 w-56 rounded-md border border-border-default bg-surface-card',
          'px-3 pr-8 text-sm text-text-primary placeholder:text-text-muted',
          'focus:border-brand-accent focus:outline-none focus:ring-2 focus:ring-brand-accent/20',
          className,
        ]
          .filter(Boolean)
          .join(' ')}
        {...props}
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange('')}
          aria-label="Clear"
          className="absolute right-2 text-text-muted hover:text-text-primary"
        >
          <CloseIcon sx={{ fontSize: 16 }} />
        </button>
      )}
    </div>
  )
}