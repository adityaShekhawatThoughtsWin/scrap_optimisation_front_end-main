export const Location = {
  Vijayanagar: 'VIJAYANAGAR',
  Dolvi: 'DOLVI',
  Bpsl: 'BPSL',
  Raigarh: 'RAIGARH',
} as const

export type Location = (typeof Location)[keyof typeof Location]

export const LOCATION_LABELS: Record<Location, string> = {
  [Location.Vijayanagar]: 'Vijayanagar',
  [Location.Dolvi]: 'Dolvi',
  [Location.Bpsl]: 'BPSL',
  [Location.Raigarh]: 'Raigarh',
}

export const LOCATION_OPTIONS = (Object.values(Location) as Location[]).map(
  (value) => ({
    value,
    label: LOCATION_LABELS[value],
  }),
)
