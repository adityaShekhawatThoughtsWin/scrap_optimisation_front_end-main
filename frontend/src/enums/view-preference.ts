export const ViewPreference = {
  Location: 'LOCATION',
  Plant: 'PLANT',
} as const

export type ViewPreference =
  (typeof ViewPreference)[keyof typeof ViewPreference]

export const VIEW_PREFERENCE_LABELS: Record<ViewPreference, string> = {
  [ViewPreference.Location]: 'Location View',
  [ViewPreference.Plant]: 'Plant View',
}
