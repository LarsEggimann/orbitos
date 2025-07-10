import React from 'react'
import { TextField, MenuItem, Stack } from '@mui/material'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
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
  axis,
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
      <ExecQueryButton
        onClick={onConnect}
        disabled={connectionStatus === 'connected'}
      >
        Connect
      </ExecQueryButton>
      <ExecQueryButton
        onClick={onDisconnect}
        disabled={connectionStatus === 'disconnected'}
        color='warning'
      >
        Disconnect
      </ExecQueryButton>
    </Stack>
  )
}
