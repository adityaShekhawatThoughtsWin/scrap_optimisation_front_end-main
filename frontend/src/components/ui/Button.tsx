import type { ButtonHTMLAttributes, ReactNode } from 'react'

type ButtonVariant = 'primary' | 'outline' | 'ghost' | 'secondary'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
  fullWidth?: boolean
  children: ReactNode
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-gradient-to-b from-[var(--color-button-sign-in-from)] to-[var(--color-button-sign-in-to)] text-text-inverse hover:opacity-90',
  outline:
    'border border-border-default bg-surface-card text-text-primary hover:bg-surface-page',
  ghost: 'bg-transparent text-brand-accent hover:underline',
  secondary: 'bg-gradient-to-b from-[var(--color-button-dark-sign-in-from)] to-[var(--color-button-dark-sign-in-to)] text-text-inverse hover:opacity-90',
}

export function Button({
  variant = 'primary',
  fullWidth = false,
  className = '',
  children,
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={[
        'inline-flex h-11 items-center justify-center rounded-lg px-4 text-base font-medium transition-opacity',
        'focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-brand-accent',
        'disabled:cursor-not-allowed disabled:opacity-50',
        variantClasses[variant],
        fullWidth ? 'w-full' : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...props}
    >
      {children}
    </button>
  )
}
