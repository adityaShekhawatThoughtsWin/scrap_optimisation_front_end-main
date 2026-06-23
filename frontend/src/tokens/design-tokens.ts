/**
 * Design tokens synced from Figma (login screen).
 * CSS variables in index.css mirror these values for Tailwind utilities.
 */
export const colors = {
  brand: {
    primary: '#17479e',
    primaryDark: '#0d2d6b',
    accent: '#1d6ce8',
    danger: '#d71920',
    subtitle: '#bedbff',
  },
  text: {
    primary: '#0a0a0a',
    heading: '#101828',
    secondary: '#717182',
    muted: '#99a1af',
    label: '#6a7282',
    option: '#364153',
    dropdown: '#4c525d',
    inverse: '#ffffff',
    inverseMuted: 'rgba(255, 255, 255, 0.8)',
    inverseDisabled: 'rgba(255, 255, 255, 0.6)',
  },
  border: {
    default: '#e5e7eb',
    checkbox: '#b5b5be',
    dropdown: '#e0e0e0',
    selected: '#78a5f8',
  },
  surface: {
    page: '#f9fafb',
    card: '#ffffff',
    input: '#f9fafb',
    iconMuted: '#f3f3f3',
    glass: 'rgba(255, 255, 255, 0.1)',
    glassBorder: 'rgba(255, 255, 255, 0.2)',
    glassButton: 'rgba(255, 255, 255, 0.24)',
    icon: 'rgba(255, 255, 255, 0.2)',
    decor: 'rgba(255, 255, 255, 0.32)',
  },
  button: {
    signInFrom: 'rgba(23, 71, 158, 0.6)',
    signInTo: 'rgba(13, 45, 107, 0.6)',
  },
} as const

export const typography = {
  fontFamily: {
    sans: "'Inter', system-ui, -apple-system, sans-serif",
  },
  fontSize: {
    xs: '0.875rem',
    sm: '1rem',
    md: '1.125rem',
    lg: '1.875rem',
    xl: '1.875rem',
    '2xl': '2.25rem',
    display: '1.875rem',
  },
  fontWeight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.625,
  },
} as const

export const spacing = {
  cardPadding: '3rem',
  formGap: '1.5rem',
  sectionGap: '1.625rem',
} as const

export const radius = {
  sm: '0.5rem',
  md: '0.625rem',
  lg: '0.875rem',
  xl: '1rem',
} as const

export const shadow = {
  card: '0px 10px 7.5px rgba(0, 0, 0, 0.1), 0px 4px 3px rgba(0, 0, 0, 0.1)',
  preferenceCard:
    '0px 10px 15px rgba(0, 0, 0, 0.1), 0px 4px 6px rgba(0, 0, 0, 0.1)',
  dropdown: '0px 4px 4px rgba(0, 0, 0, 0.25)',
} as const

export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
} as const
