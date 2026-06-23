export type UploadStatus = 'idle' | 'uploading' | 'uploaded' | 'error'

export type DownloadStepConfig = {
  id: string
  title: string
}

export type UploadStepConfig = {
  id: string
  stepNumber: number
  title: string
  optional?: boolean
  outputNote?: string | null
  footerNote?: string | null
  /** When a step needs more than one file (e.g. step 1). Defaults to [id]. */
  fileSlotIds?: string[]
}

export const UPLOAD_STEPS: UploadStepConfig[] = [
  {
    id: 'heat-query-all',
    stepNumber: 1,
    title: 'heat query all and heat query chem file',
    optional: false,
    outputNote: 'Output of Step 1: Scrap chem file',
    footerNote: null,
    fileSlotIds: ['heat-query-all', 'heat-query-chem'],
  },
  {
    id: 'scrap-chem',
    stepNumber: 2,
    title: 'scrap chem file',
    optional: false,
    outputNote: null,
    footerNote: null,
  },
  {
    id: 'heat-query-scheduled-heats',
    stepNumber: 3,
    title: 'heat query (scheduled heats) file',
    optional: false,
    outputNote: null,
    footerNote: null,
  },
  {
    id: 'scrap-data-daily-inventory',
    stepNumber: 4,
    title: 'scrap data daily inventory',
    optional: false,
    outputNote: null,
    footerNote: null,
  },
  {
    id: 'met-grade-list',
    stepNumber: 5,
    title: 'met grade list',
    optional: true,
    footerNote: "If not uploaded, last uploaded file will be used.",
    outputNote: null,
  },
]

export const DOWNLOAD_STEPS: DownloadStepConfig[] = [
  {
    id: 'heat-query-all',
    title: 'heat query all file',
  },
  {
    id: 'heat-query-chem',
    title: 'heat query chem file',
  },
  {
    id: 'scrap-chem',
    title: 'scrap chem file',
  },
  {
    id: 'heat-query-scheduled-heats',
    title: 'heat query (scheduled heats) file',
  },
  {
    id: 'scrap-data-daily-inventory',
    title: 'scrap data daily inventory',
  },
  {
    id: 'met-grade-list',
    title: 'met grade list',
  },
]

export function getFileSlotIds(step: UploadStepConfig): string[] {
  return step.fileSlotIds ?? [step.id]
}

export function getAllFileSlotIds(steps: UploadStepConfig[] = UPLOAD_STEPS): string[] {
  return steps.flatMap(getFileSlotIds)
}

export function createEmptyStepFiles(steps: UploadStepConfig[] = UPLOAD_STEPS): Record<string, File | null> {
  return Object.fromEntries(getAllFileSlotIds(steps).map((slotId) => [slotId, null]))
}

export function createEmptyUploadStatuses(
  steps: UploadStepConfig[] = UPLOAD_STEPS,
): Record<string, UploadStatus> {
  return Object.fromEntries(getAllFileSlotIds(steps).map((slotId) => [slotId, 'idle']))
}

export function isStepComplete(
  step: UploadStepConfig,
  uploadStatuses: Record<string, UploadStatus>,
): boolean {
  return getFileSlotIds(step).every((slotId) => uploadStatuses[slotId] === 'uploaded')
}

export function isStepEnabled(
  stepNumber: number,
  uploadStatuses: Record<string, UploadStatus>,
  steps: UploadStepConfig[] = UPLOAD_STEPS,
): boolean {
  if (stepNumber === 1) return true
  const previousStep = steps.find((s) => s.stepNumber === stepNumber - 1)
  return previousStep ? isStepComplete(previousStep, uploadStatuses) : false
}

export function areRequiredFilesUploaded(
  uploadStatuses: Record<string, UploadStatus>,
  steps: UploadStepConfig[] = UPLOAD_STEPS,
): boolean {
  return steps.filter((s) => !s.optional).every((step) => isStepComplete(step, uploadStatuses))
}

export const YESTERDAY_FILES = UPLOAD_STEPS.map((step) => ({
  id: step.id,
  name: step.title,
}))

export const ACCEPTED_FILE_TYPES = '.xlsx,.xls,.csv'
