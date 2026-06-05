import * as React from 'react'
import DownloadIcon from '@mui/icons-material/Download'

import TextField from '@mui/material/TextField'
import Stack from '@mui/material/Stack'
import PrestyledButton from './PrestyledButton'

// created with ChatJypidyyi

export type DownloadCSVButtonProps = {
  /**
   * The data to export. Should be an object of arrays, e.g. { timestamp: [...], current: [...] }
   */
  data: Record<string, any[]>
  /**
   * Optional: Default filename (without extension). If not provided, current date is used.
   */
  defaultFilename?: string
  /**
   * Optional callback that will be executed before the CSV is created.
   * Can be used to trigger a query/refetch. If it returns data (object or array of files),
   * Signature: () => Promise<void | Record<string, any[]> | Array<{ filename?: string; data: Record<string, any[]> }>>
   */
  beforeDownload?: () => Promise<
    | void
    | Record<string, any[]>
  >
  /**
   * Optional: Button label override
   */
  buttonLabel?: string
}

function toCSV(data: Record<string, any[]>): string {
  const keys = Object.keys(data)
  if (keys.length === 0) return ''
  const length = data[keys[0]].length
  // CSV header
  let csv = keys.join(',') + '\n'
  // Data rows
  for (let i = 0; i < length; i++) {
    csv +=
      keys
        .map((k) => {
          const v = data[k][i]
          if (
            typeof v === 'string' &&
            (v.includes(',') || v.includes('"') || v.includes('\n'))
          ) {
            return '"' + v.replace(/"/g, '""') + '"'
          }
          return v ?? ''
        })
        .join(',') + '\n'
  }
  return csv
}

const DownloadCSVButton: React.FC<DownloadCSVButtonProps> = ({
  data,
  defaultFilename,
  beforeDownload,
  buttonLabel = 'Download CSV',
}) => {
  const [prefix, setPrefix] = React.useState('')
  const [loading, setLoading] = React.useState(false)

  const downloadOne = (dataObj: Record<string, any[]>, filenameBase: string) => {
    const csv = toCSV(dataObj)
    const filename = `${prefix ? prefix + '_' : ''}${filenameBase}.csv`
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleDownload = async () => {
    // if no data and no prefetch provided, nothing to do
    const hasData =
      data &&
      Object.values(data).some((arr) => Array.isArray(arr) && arr.length > 0)
    const canTriggerPrefetch = typeof beforeDownload === 'function'
    if (!hasData && !canTriggerPrefetch) return

    setLoading(true)
    try {
      // If we already have data, use it. Otherwise, run beforeDownload and expect a single dataset.
      let dataset: Record<string, any[]> | undefined = undefined

      if (hasData) {
        dataset = data
      } else if (beforeDownload) {
        const result = await beforeDownload()
        if (result && typeof result === 'object') {
          dataset = result
        }
      }

      if (!dataset) return

      const base = defaultFilename || new Date().toISOString().split('.')[0]
      downloadOne(dataset, base)
    } finally {
      setLoading(false)
    }
  }

  // check if any data is present
  const hasData =
    data &&
    Object.values(data).some((arr) => Array.isArray(arr) && arr.length > 0)
  const canTriggerPrefetch = typeof beforeDownload === 'function'

  return (
    <Stack direction='row' spacing={2} sx={{ alignItems: 'center' }}>
      <TextField
        label='Filename Prefix'
        value={prefix}
        onChange={(e) => setPrefix(e.target.value)}
        size='small'
        variant='outlined'
      />
      <PrestyledButton
        onClick={handleDownload}
        disabled={!(hasData || canTriggerPrefetch) || loading}
        startIcon={<DownloadIcon />}
      >
        {loading ? 'Preparing...' : buttonLabel}
      </PrestyledButton>
    </Stack>
  )
}

export default DownloadCSVButton
