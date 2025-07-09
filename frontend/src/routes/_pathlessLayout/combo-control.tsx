import { useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Stack from '@mui/material/Stack'
import MenuItem from '@mui/material/MenuItem'
import Chip from '@mui/material/Chip'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Select from '@mui/material/Select'
import type { SelectChangeEvent } from '@mui/material/Select'

import ExecQueryButton from '~/components/ui/ExecQueryButton'
import Chopperwheel from '~/components/chopperwheel/chopperwheel'
import Electrometer from '~/components/electrometer/electrometer'
import {
  Chopperwheel as ChopperwheelService,
  Electrometer as ElectrometerService,
} from '~/generated'
import { useExecQueryHelper } from '~/utils/ExecQueryHelper'
import Divider from '@mui/material/Divider'

export const Route = createFileRoute('/_pathlessLayout/combo-control')({
  component: RouteComponent,
})

type DeviceType = 'chopperwheel' | 'electrometer_1' | 'electrometer_2'

interface DeviceOption {
  value: DeviceType
  label: string
}

const deviceOptions: DeviceOption[] = [
  { value: 'chopperwheel', label: 'Chopperwheel' },
  { value: 'electrometer_1', label: 'Electrometer 1' },
  { value: 'electrometer_2', label: 'Electrometer 2' },
]

function RouteComponent() {
  const [selectedDevices, setSelectedDevices] = useState<DeviceType[]>([])

  const { executeQuery } = useExecQueryHelper()

  const handleDevicesChange = (event: SelectChangeEvent<typeof selectedDevices>) => {
    const value = event.target.value
    setSelectedDevices(typeof value === 'string' ? value.split(',') as DeviceType[] : value)
  }

  const executeActions = async () => {
    const promises = selectedDevices.map(async (device) => {
      if (device === 'chopperwheel') {
        return await executeQuery(ChopperwheelService.chopperwheelFlashBeamChopperWheel)
      } else if (device === 'electrometer_1') {
        return await executeQuery(() => ElectrometerService.electrometerStartTriggerBasedMeasurement({
          path: { device_id: 1 },
        }))
      } else if (device === 'electrometer_2') {
        return await executeQuery(() => ElectrometerService.electrometerStartTriggerBasedMeasurement({
          path: { device_id: 2 },
        }))
      }
    })
    await Promise.all(promises)
  }

  const getActionButtonText = () => {
    const chopperwheelSelected = selectedDevices.includes('chopperwheel')
    const electrometerSelected = selectedDevices.some(d => d.startsWith('electrometer'))

    if (chopperwheelSelected && electrometerSelected) {
      return `Execute Flash Action (${selectedDevices.length} devices)`
    } else if (chopperwheelSelected) {
      return 'Flash Beam'
    } else if (electrometerSelected) {
      return `Start Trigger Measurement (${selectedDevices.filter(d => d.startsWith(`electrometer`)).length} devices)`
    }
    return 'Execute Actions'
  }

  const renderSelectedDevices = () => {
    if (selectedDevices.length === 0) {
      return (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="text.secondary">
            No devices selected. Please select devices above.
          </Typography>
        </Box>
      )
    }

    return (
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, gap: 3 }}>
        {selectedDevices.map((device) => (
          <Box
            key={device}
            sx={{
              flex: 1,
              minWidth: 0,
              overflow: 'hidden',
              gap: 2,
            }}
          >
            {device === 'chopperwheel' && <Chopperwheel />}
            {device === 'electrometer_1' && <Electrometer deviceId={1} />}
            {device === 'electrometer_2' && <Electrometer deviceId={2} />}
          </Box>
        ))}
      </Box>
    )
  }

  return (
    <Box sx={{ bgcolor: 'background.paper' }}>
      <Stack
        direction='row'
        sx={{ alignItems: 'center', justifyContent: 'space-between'}}
      >
        <Typography variant='h5'>
          Combo Control
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormControl sx={{ minWidth: 300 }}>
            <InputLabel id='input-label'>Select Devices for Actions</InputLabel>
            <Select
              multiple
              size='small'
              value={selectedDevices}
              onChange={handleDevicesChange}
              label="Select Devices for Actions"
              labelId='input-label'
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip
                      key={value}
                      label={deviceOptions.find(opt => opt.value === value)?.label || value}
                      size="small"
                    />
                  ))}
                </Box>
              )}
            >
              {deviceOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>


          <ExecQueryButton
            onClick={executeActions}
            color={selectedDevices.includes('chopperwheel') ? 'primary' : 'secondary'}
            sx={{ minWidth: 200 }}
            disabled={selectedDevices.length === 0}
          >
            {getActionButtonText()}
          </ExecQueryButton>
        </Box>

      </Stack>
      <Divider sx={{ m: 1 }} />

      {renderSelectedDevices()}
    </Box>
  )
}
