import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined'
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import type { DownloadStepConfig, UploadStepConfig } from './uploadStepsConfig'

type UploadSidebarProps = {
  steps: UploadStepConfig[]
  yesterdaySteps: DownloadStepConfig[]
  yesterdayDateLabel: string
  onDownloadYesterday: (stepId: string) => void
}

export function UploadSidebar({
  steps,
  yesterdaySteps,
  yesterdayDateLabel,
  onDownloadYesterday,
}: UploadSidebarProps) {
  return (
    <aside className="w-full shrink-0 rounded-xl border border-border-default bg-surface-card p-5 lg:max-w-sm">
      <section>
        <h2 className="text-lg font-semibold text-text-heading">Files to Upload</h2>
        <p className="mt-1 text-sm text-text-secondary">
          Upload the following files in the given order.
        </p>
        <ol className="mt-4 space-y-4">
          {steps.map((step) => (
            <li key={step.id} className="flex gap-3">
              <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-brand-primary text-xs font-semibold text-text-inverse">
                {step.stepNumber}
              </span>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  {step.optional && (
                    <span className="rounded-full bg-brand-subtitle/40 px-2 py-0.5 text-xs font-medium text-brand-primary">
                      Optional
                    </span>
                  )}
                  <div className="flex flex-col items-start">
                    <span className="text-sm font-medium text-text-heading">{step.title}</span>
                    <span className="text-xs font-medium text-text-secondary">Excel / CSV</span>
                  </div>
                </div>
                {step.outputNote && (
                  <div className=" rounded-lg border border-brand mt-1 bg-brand-subtitle/20 px-3 py-2 text-xs font-bold text-brand-primary">
                  {step.outputNote}
                </div>
                )}
                {step.footerNote && (
                  <p className="mt-1 text-xs text-text-secondary">{step.footerNote}</p>
                )}
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="mt-8 border-t border-border-default pt-6">
        <h2 className="text-lg font-semibold text-text-heading">Download Last Uploaded Files</h2>
        <p className="mt-1 text-sm text-text-secondary">
          Download the files uploaded last ({yesterdayDateLabel}).
        </p>
        <ul className="mt-4 space-y-2">
          {yesterdaySteps.map((step) => (
            <li key={step.id}>
              <button
                type="button"
                onClick={() => onDownloadYesterday(step.id)}
                className="flex w-full items-center gap-3 border border-border-default rounded-lg bg-amber-50 px-3 py-2.5 text-left transition-colors cursor-pointer hover:bg-amber-100"
              >
                <DescriptionOutlinedIcon
                  className="text-amber-500"
                  sx={{ fontSize: 22 }}
                  aria-hidden
                />
                <span className="min-w-0 flex-1 truncate text-sm text-text-heading">
                  {step.title}
                </span>
                <FileDownloadOutlinedIcon
                  className="shrink-0 text-amber-600"
                  sx={{ fontSize: 22 }}
                  aria-hidden
                />
              </button>
            </li>
          ))}
        </ul>
        <p className="mt-4 flex items-start gap-1.5 text-xs text-text-secondary">
          <InfoOutlinedIcon sx={{ fontSize: 14 }} className="mt-0.5 shrink-0" aria-hidden />
          Files are available for last uploaded only.
        </p>
      </section>
    </aside>
  )
}
