import type { InputHTMLAttributes } from 'react'

type CheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & {
  label: string
}

export function Checkbox({ label, id, className = '', ...props }: CheckboxProps) {
  const checkboxId = id ?? label.toLowerCase().replace(/\s+/g, '-')

  return (
    <label
      htmlFor={checkboxId}
      className={['flex cursor-pointer items-center gap-2', className]
        .filter(Boolean)
        .join(' ')}
    >
      <input
        id={checkboxId}
        type="checkbox"
        className="size-3.5 shrink-0 rounded-sm border border-border-checkbox bg-surface-card accent-brand-primary"
        {...props}
      />
      <span className="text-sm text-text-primary">{label}</span>
    </label>
  )
}
