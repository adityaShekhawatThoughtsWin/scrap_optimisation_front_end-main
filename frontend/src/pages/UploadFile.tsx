import CircularProgress from '@mui/material/CircularProgress'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import PlayCircleOutlinedIcon from '@mui/icons-material/PlayCircleOutlined'
import { useMemo, useState } from 'react'
import { UploadSidebar } from '../components/upload/UploadSidebar'
import { UploadStep } from '../components/upload/UploadStep'
import {
    DOWNLOAD_STEPS,
  UPLOAD_STEPS,
  areRequiredFilesUploaded,
  createEmptyStepFiles,
  createEmptyUploadStatuses,
  getFileSlotIds,
  isStepEnabled,
} from '../components/upload/uploadStepsConfig'
import uploadService from '../service/upload.service'
import {
  downloadApiFile,
  downloadModelOutputFile,
  getUploadRecordId,
  tryDownloadModelOutput,
  type PlannerFileIds,
} from '../utils/FileRead'
import modelService from '../service/model.service'
import downloadService from '../service/download.service'

function formatYesterdayLabel(date: Date): string {
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function UploadFile() {
  const [stepFiles, setStepFiles] = useState(createEmptyStepFiles)
  const [uploadStatuses, setUploadStatuses] = useState(createEmptyUploadStatuses)
  const [heatQueryAllId, setHeatQueryAllId] = useState<number | null>(null)
  const [heatQueryChemId, setHeatQueryChemId] = useState<number | null>(null)
  const [plannerFileIds, setPlannerFileIds] = useState<PlannerFileIds | null>(null)
  const [isPlannerRunning, setIsPlannerRunning] = useState(false)


  const yesterdayLabel = useMemo(() => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    return formatYesterdayLabel(yesterday)
  }, [])

  const requiredStepsUploaded = areRequiredFilesUploaded(uploadStatuses)

  const setSlotUploadStatus = (slotId: string, status: 'idle' | 'uploading' | 'uploaded' | 'error') => {
    setUploadStatuses((prev) => ({ ...prev, [slotId]: status }))
  }

  const handleFileSelect = async (slotId: string, file: File | null) => {
    if (!file) return

    setStepFiles((prev) => ({ ...prev, [slotId]: file }))
    setSlotUploadStatus(slotId, 'uploading')

    const formData = new FormData()
    formData.append('file', file)

    const pairedId =
      slotId === 'heat-query-all'
        ? heatQueryChemId
        : slotId === 'heat-query-chem'
          ? heatQueryAllId
          : null
    if (pairedId != null) {
      formData.append('pairedId', pairedId.toString())
    }

    try {
      switch (slotId) {
        case 'heat-query-all': {
          const response = await uploadService.uploadHeatQueryAll(formData)
          const recordId = getUploadRecordId(response?.data)
          if (recordId != null) setHeatQueryAllId(recordId)
          tryDownloadModelOutput(response?.data)
          break
        }
        case 'heat-query-chem': {
          const response = await uploadService.uploadHeatChem(formData)
          const recordId = getUploadRecordId(response?.data)
          if (recordId != null) setHeatQueryChemId(recordId)
          tryDownloadModelOutput(response?.data)
          break
        }
        case 'scrap-chem': {
          const scrapChemResponse = await uploadService.uploadScrapChem(formData)
          const scrapChemRecordId = getUploadRecordId(scrapChemResponse?.data)
          if (scrapChemRecordId != null) {
            setPlannerFileIds((prev) => ({ ...prev, scrapChemId: scrapChemRecordId }))
          }
          break
        }
        case 'heat-query-scheduled-heats': {
          const heatQueryScheduleResponse = await uploadService.uploadHeatQuerySchedule(formData)
          const heatQueryScheduleRecordId = getUploadRecordId(heatQueryScheduleResponse?.data)
          if (heatQueryScheduleRecordId != null) {
            setPlannerFileIds((prev) => ({ ...prev, heatQueryScheduleId: heatQueryScheduleRecordId }))
          }
          break
        }
        case 'scrap-data-daily-inventory': {
          const scrapDataInventoryResponse = await uploadService.uploadScrapDataInventory(formData)
          const scrapDataInventoryRecordId = getUploadRecordId(scrapDataInventoryResponse?.data)
          if (scrapDataInventoryRecordId != null) {
            setPlannerFileIds((prev) => ({ ...prev, scrapInventoryId: scrapDataInventoryRecordId }))
          }
          break
        }
        case 'met-grade-list': {
          const gradeListResponse = await uploadService.uploadGradeList(formData)
          const gradeListRecordId = getUploadRecordId(gradeListResponse?.data)
          if (gradeListRecordId != null) {
            setPlannerFileIds((prev) => ({ ...prev, gradeListId: gradeListRecordId }))
          }
          break
        }
      }
      setSlotUploadStatus(slotId, 'uploaded')
    } catch {
      setSlotUploadStatus(slotId, 'error')
    }
  }

  const handleRunPlanner = async () => {
    if (!requiredStepsUploaded || isPlannerRunning || !plannerFileIds) return

    setIsPlannerRunning(true)
    try {
      const response = await modelService.runModel(plannerFileIds)
      const outputFile = response?.data?.output_file
      if (response?.data?.success && outputFile?.content_base64) {
        downloadModelOutputFile(outputFile)
      }
    } catch (error) {
      console.error('Error running planner', error)
    } finally {
      setIsPlannerRunning(false)
    }
  }

  const handleDownloadYesterday = async (stepId: string) => {
    try {
      let response
      switch (stepId) {
        case 'heat-query-all':
          response = await downloadService.downloadHeatQueryAll()
          break
        case 'heat-query-chem':
          response = await downloadService.downloadHeatChem()
          break
        case 'scrap-chem':
          response = await downloadService.downloadScrapChem()
          break
        case 'heat-query-scheduled-heats':
          response = await downloadService.downloadHeatQuerySchedule()
          break
        case 'scrap-data-daily-inventory':
          response = await downloadService.downloadScrapDataInventory()
          break
        case 'met-grade-list':
          response = await downloadService.downloadGradeList()
          break
        default:
          console.error('Invalid step ID', stepId)
          return
      }
      downloadApiFile(response)
    } catch (error) {
      console.error('Error downloading yesterday file', error)
    }
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-background px-7 py-6">
      <div className="mx-auto flex flex-col gap-8 lg:flex-row lg:items-start">
        <main className="min-w-0 flex-1">
          <header>
            <h1 className="text-2xl font-bold text-text-heading">
              Upload Files (One by One in Order)
            </h1>
            <p className="mt-2 text-sm text-text-secondary">
              Please upload the files in the given sequence. You can download yesterday&apos;s
              files from the right.
            </p>
          </header>

          <div className="relative z-10 mt-8 flex flex-col gap-3">
            <div className="absolute top-10 left-8 z-1 h-[calc(100%-140px)] w-0.5 bg-brand-primary" />
            {UPLOAD_STEPS.map((step) => (
              <UploadStep
                key={step.id}
                stepNumber={step.stepNumber}
                title={step.title}
                optional={step.optional}
                outputNote={step.outputNote}
                footerNote={step.footerNote}
                fileSlotIds={getFileSlotIds(step)}
                files={stepFiles}
                uploadStatuses={uploadStatuses}
                onFileSelect={handleFileSelect}
                disabled={!isStepEnabled(step.stepNumber, uploadStatuses)}
              />
            ))}
          </div>

          <div className="mt-2 flex items-start gap-2 rounded-lg border border-border-default px-4 py-3 text-sm font-bold text-brand-danger">
            <InfoOutlinedIcon className="shrink-0" sx={{ fontSize: 18 }} aria-hidden />
            Note:
            <span className="font-normal text-text-primary">
              Upload files one by one in the above order for accurate scrap mix planning.
            </span>
          </div>

          <div className="mt-8 flex flex-col items-center">
            <button
              type="button"
              disabled={!requiredStepsUploaded || isPlannerRunning}
              onClick={handleRunPlanner}
              className={[
                'inline-flex items-center gap-2 rounded-xl px-8 py-3.5 text-base font-semibold text-text-inverse transition-opacity',
                'focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-border-selected',
                requiredStepsUploaded && !isPlannerRunning
                  ? 'cursor-pointer bg-linear-to-t from-green-700 to-green-500 hover:opacity-90'
                  : 'cursor-not-allowed bg-text-muted',
              ].join(' ')}
            >
              {isPlannerRunning ? (
                <CircularProgress size={24} sx={{ color: 'inherit' }} aria-hidden />
              ) : (
                <PlayCircleOutlinedIcon sx={{ fontSize: 24 }} aria-hidden />
              )}
              {isPlannerRunning ? 'Running Planner...' : 'Run Planner & Download Daily Plan'}
            </button>
            <p className="mt-3 text-sm text-text-secondary">
              All required files must be uploaded to enable this button.
            </p>
          </div>
        </main>

        <UploadSidebar
          steps={UPLOAD_STEPS}
          yesterdaySteps={DOWNLOAD_STEPS}
          yesterdayDateLabel={yesterdayLabel}
          onDownloadYesterday={handleDownloadYesterday}
        />
      </div>
    </div>
  )
}

export default UploadFile
