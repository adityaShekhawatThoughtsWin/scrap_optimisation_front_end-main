export interface ModelOutputFile {
  filename: string
  content_base64: string
  mime_type: string
}

export interface HeatUploadResponseData {
  id?: number
  modelResult?: {
    output_file?: ModelOutputFile
  }
}

/** Shape returned by GET /download/* endpoints */
export interface ApiFileDownload {
  filename: string
  mimeType?: string
  data?: string
}

export function saveBlobAsFile(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

/** Decode base64 file payload from GET /download/* responses and save locally */
export function downloadApiFile(file: ApiFileDownload | null | undefined): void {
  if (!file?.filename || !file.data) return

  const binary = atob(file.data)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  const blob = new Blob([bytes], { type: file.mimeType ?? 'application/octet-stream' })
  saveBlobAsFile(blob, file.filename)
}

/** Decode base64 `output_file` from heat-chem / model upload responses and save locally */
export function downloadModelOutputFile(outputFile: ModelOutputFile): void {
  const binary = atob(outputFile.content_base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  const blob = new Blob([bytes], { type: outputFile.mime_type })
  saveBlobAsFile(blob, outputFile.filename)
}

export function getUploadRecordId(
  data: HeatUploadResponseData | undefined
): number | undefined {
  if (!data) return undefined
  if (data.id != null) return data.id
  return undefined
}

/** When both heat files are paired, the API may include a model Excel in `modelResult.output_file`. */
export function tryDownloadModelOutput(data: HeatUploadResponseData | undefined): void {
  const outputFile = data?.modelResult?.output_file
  if (outputFile?.content_base64) {
    downloadModelOutputFile(outputFile)
  }
}

export interface PlannerFileIds {
  scrapChemId?: number
  heatQueryScheduleId?: number
  scrapInventoryId?: number
  gradeListId?: number
}