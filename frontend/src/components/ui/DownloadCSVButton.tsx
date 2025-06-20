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
}) => {
  const [prefix, setPrefix] = React.useState('')

  const handleDownload = () => {
    if (!data) return
    const csv = toCSV(data)
    const base = defaultFilename || new Date().toISOString().split('.')[0]
    const filename = `${prefix ? prefix + '_' : ''}${base}.csv`
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  // check if any data is present
  const hasData =
    data &&
    Object.values(data).some((arr) => Array.isArray(arr) && arr.length > 0)

  return (
    <Stack direction='row' spacing={2} alignItems='center'>
      <TextField
        label='Filename Prefix'
        value={prefix}
        onChange={(e) => setPrefix(e.target.value)}
        size='small'
        variant='outlined'
      />
      <PrestyledButton
        onClick={handleDownload}
        disabled={!hasData}
        startIcon={<DownloadIcon />}
      >
        Download CSV
      </PrestyledButton>
    </Stack>
  )
}

export default DownloadCSVButton
