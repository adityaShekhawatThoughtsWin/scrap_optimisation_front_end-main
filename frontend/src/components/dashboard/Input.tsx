import CachedIcon from '@mui/icons-material/Cached'           // Refresh icon
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined' // Download icon
import SaveOutlinedIcon from '@mui/icons-material/SaveOutlined'       // Save icon
import { useState } from 'react'                           // React hook for state management
import { Button } from '../ui/Button'                         // Custom Button component
import { ClearableInput } from '../ui/ClearableInput'             // Custom ClearableInput component
import { InputTable } from '../ui/InputTable'                   // Custom InputTable component
import type { TableColumn } from '../ui/InputTable'             // Type definition for TableColumn

// ─── Table Column Definitions ─────────────────────────────────────────────────
// Defines the structure of the columns for the InputTable.
const INPUT_COLUMNS: TableColumn[] = [
  { key: 'srNo', label: 'Sr No' },
  { key: 'openingElements', label: 'Opening Elements', filterable: true },
  { key: 'opening', label: 'Opening', filterable: true },
  {
    key: 'target',
    label: 'Target',
    children: [
      { key: 'targetMin', label: 'Min', filterable: true },
      { key: 'targetMax', label: 'Max', filterable: true },
    ],
  },
  { key: 'scrapName', label: 'Scrap Name', filterable: true },
  { key: 'modelSuggested', label: 'Model Suggested (MT)', filterable: true },
  { key: 'predictedChemistry', label: 'Predicted Chemistry (MT)', filterable: true },
  { key: 'actualAddition', label: 'Actual Addition', filterable: true },
  { key: 'actualChemistry', label: 'Actual Chemistry', filterable: true },
]

// ─── Main Input Component ─────────────────────────────────────────────────────
function Input() {

  const [heatId, setHeatId] = useState('')
  const [sequenceId, setSequenceId] = useState('')
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Handler for the Refresh button click.
  function handleRefreshActuals() {
    setIsRefreshing(true)
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  const rowH = 'h-[40px]'
  const iconBtn =
    `flex ${rowH} w-[40px] items-center justify-center rounded-lg transition-colors`

  const textBtn =
    `${rowH} px-3 flex items-center text-sm font-medium`

  return (
    <div className="flex flex-col gap-4 bg-surface-card px-6 py-5">
      <div className="flex flex-col gap-3">
        <div className={`flex items-center justify-between ${rowH}`}>
          <div className={`flex items-center gap-3 ${rowH}`}>

            <span className={`w-28 text-sm font-medium flex items-center ${rowH}`}>
              Heat ID
            </span>

            <ClearableInput
              value={heatId}
              onChange={setHeatId}
              className={rowH}
            />

            <button className={`${textBtn} text-text-primary hover:underline`}>
              Fetch Data
            </button>

            <button className={`${textBtn} text-brand-accent hover:underline`}>
              Go to Next Heat ID
            </button>

          </div>

          <div className="flex items-center gap-2">

            <button className={`${iconBtn} border border-[#FDEBBC] text-[#E09800]`}>
              <SaveOutlinedIcon sx={{ fontSize: 18 }} />
            </button>

            <button className={`${iconBtn} border border-[#DCFCE7] text-[#16A34A]`}>
              <FileDownloadOutlinedIcon sx={{ fontSize: 18 }} />
            </button>

          </div>
        </div>

        <div className={`flex items-center justify-between ${rowH}`}>

          <div className={`flex items-center gap-3 ${rowH}`}>

            <span className={`w-28 text-sm font-medium flex items-center ${rowH}`}>
              Sequence ID
            </span>

            <ClearableInput
              value={sequenceId}
              onChange={setSequenceId}
              className={rowH}
            />

            <Button
              className="
                h-[40px]
                px-12
                text-xs uppercase tracking-widest
                text-white
                bg-[linear-gradient(174.84deg,_#16A34A_29.64%,_#083D1C_231.54%)] // Green gradient background
                shadow-[3px_3px_11.3px_0px_#00000040]
              "
            >
              Optimize
            </Button>

          </div>

          <button
            onClick={handleRefreshActuals}
            className="
              h-[40px]
              px-12
              flex items-center gap-2
              rounded-md
              bg-blue-50 // Light blue background
              text-sm font-medium text-brand-primary // Accent blue text color
              hover:bg-blue-100 // Lighter blue on hover
            "
          >
            Refresh Actuals
            <CachedIcon sx={{ fontSize: 18 }} className={isRefreshing ? 'animate-spin' : ''} /> {/* Refresh icon with optional spin */}
          </button>

        </div>
      </div>

      <InputTable columns={INPUT_COLUMNS} rowCount={10} />
    </div>
  )
}

export default Input