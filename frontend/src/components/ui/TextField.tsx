import type { InputHTMLAttributes, ReactNode } from 'react'

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  icon?: ReactNode
  trailing?: ReactNode
}

export function TextField({
  label,
  icon,
  trailing,
  id,
  className = '',
  ...props
}: TextFieldProps) {
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, '-')

  return (
    <div className="flex w-full flex-col gap-2.5">
      <label
        htmlFor={inputId}
        className="text-sm font-medium leading-none text-text-primary"
      >
        {label}
      </label>
      <div className="relative">
        {icon && (
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary [&_svg]:size-4">
            {icon}
          </span>
        )}
        <input
          id={inputId}
          className={[
            'h-11 w-full rounded-lg border border-border-default bg-surface-input',
            'text-sm text-text-primary placeholder:text-text-secondary',
            'focus:border-brand-accent focus:outline-none focus:ring-2 focus:ring-brand-accent/20',
            icon ? 'pl-10 pr-3' : 'px-3',
            trailing ? 'pr-10' : '',
            className,
          ]
            .filter(Boolean)
            .join(' ')}
          {...props}
        />
        {trailing && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 [&_button]:text-text-secondary">
            {trailing}
          </span>
        )}
      </div>
    </div>
  )
}
