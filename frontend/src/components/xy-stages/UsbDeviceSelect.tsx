import React from 'react'
import { TextField, MenuItem, Stack } from '@mui/material'
import ConnectionButtons from '~/components/ui/ConnectionButtons'
import type { PerformaxUsbDevice } from '~/generated'

interface UsbDeviceSelectProps {
  label: string
  axis: 'x-axis' | 'y-axis'
  value: number
  onChange: (value: number) => void
  devices?: PerformaxUsbDevice[]
  loading?: boolean
  disabled?: boolean
  connectionStatus?: string
  onConnect: () => Promise<any>
  onDisconnect: () => Promise<any>
  sx?: any
}

export const UsbDeviceSelect: React.FC<UsbDeviceSelectProps> = ({
  label,
  value,
  onChange,
  devices,
  loading = false,
  disabled = false,
  connectionStatus,
  onConnect,
  onDisconnect,
  sx = { minWidth: 250 },
}) => {
  return (
    <Stack direction='row' sx={{ alignItems: 'center', gap: 2 }}>
      <TextField
        size='small'
        variant='outlined'
        label={label}
        select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        sx={sx}
        disabled={loading || disabled}
      >
        {devices?.length === 0 && (
          <MenuItem value='' disabled>
            No USB devices found
          </MenuItem>
        )}
        {devices?.map((device) => (
          <MenuItem key={device.index} value={device.index}>
            {device.description}
          </MenuItem>
        ))}
      </TextField>
      <ConnectionButtons
        connectionStatus={connectionStatus}
        onConnect={onConnect}
        onDisconnect={onDisconnect}
      />
    </Stack>
  )
}
