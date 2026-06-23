export const Plant = {
  Pellet: 'PELLET',
  Sinter: 'SINTER',
  BlastFurnace: 'BLAST_FURNACE',
  CokeOven: 'COKE_OVEN',
} as const

export type Plant = (typeof Plant)[keyof typeof Plant]

export const PLANT_LABELS: Record<Plant, string> = {
  [Plant.Pellet]: 'Pellet',
  [Plant.Sinter]: 'Sinter',
  [Plant.BlastFurnace]: 'Blast Furnace',
  [Plant.CokeOven]: 'Coke Oven',
}

export const PLANT_OPTIONS = (Object.values(Plant) as Plant[]).map((value) => ({
  value,
  label: PLANT_LABELS[value],
}))
