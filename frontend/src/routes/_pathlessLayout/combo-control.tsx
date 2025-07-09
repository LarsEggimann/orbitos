import { useEffect, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Stack from '@mui/material/Stack'
import Divider from '@mui/material/Divider'

import ExecQueryButton from '~/components/ui/ExecQueryButton'
import Chopperwheel from '~/components/chopperwheel/chopperwheel'
import Electrometer from '~/components/electrometer/electrometer'
import {
  Chopperwheel as ChopperwheelService,
  Electrometer as ElectrometerService,
} from '~/generated'
import { useExecQueryHelper } from '~/utils/ExecQueryHelper'
import DeviceMultiSelect, { type DeviceType, defaultDeviceOptions } from '~/components/ui/DeviceMultiSelect'

export const Route = createFileRoute('/_pathlessLayout/combo-control')({
  component: RouteComponent,
})

function RouteComponent() {
  const [selectedDevices, setSelectedDevices] = useState<DeviceType[]>(() => {
    const saved = localStorage.getItem('combo_control_selected_devices')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed)) return parsed
      } catch {}
    }
    return []
  })

  useEffect(() => {
    localStorage.setItem('combo_control_selected_devices', JSON.stringify(selectedDevices))
  }, [selectedDevices])
  
  const { executeQuery } = useExecQueryHelper()
  
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
      // Avoid nested template literals
      const count = selectedDevices.filter(d => d.startsWith('electrometer')).length
      return `Start Trigger Measurement (${count} devices)`
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
          <DeviceMultiSelect
            selectedDevices={selectedDevices}
            setSelectedDevices={setSelectedDevices}
            label="Select Devices for Actions"
            minWidth={300}
          />

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
