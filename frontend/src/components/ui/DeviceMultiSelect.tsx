import React, { useEffect } from 'react'
import Box from '@mui/material/Box'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import Chip from '@mui/material/Chip'
import type { SelectChangeEvent } from '@mui/material/Select'

export type DeviceType = 'chopperwheel' | 'electrometer_1' | 'electrometer_2'

export interface DeviceOption {
    value: DeviceType
    label: string
}

export const defaultDeviceOptions: DeviceOption[] = [
    { value: 'chopperwheel', label: 'Chopperwheel' },
    { value: 'electrometer_1', label: 'Electrometer 1' },
    { value: 'electrometer_2', label: 'Electrometer 2' },
]

interface DeviceMultiSelectProps {
    selectedDevices: DeviceType[]
    setSelectedDevices: (devices: DeviceType[]) => void
    deviceOptions?: DeviceOption[]
    label?: string
    minWidth?: number
}

const DeviceMultiSelect: React.FC<DeviceMultiSelectProps> = ({
    selectedDevices,
    setSelectedDevices,
    deviceOptions = defaultDeviceOptions,
    label = 'Select Devices for Actions',
    minWidth = 300,
}) => {
    const handleDevicesChange = (event: SelectChangeEvent<typeof selectedDevices>) => {
        const value = event.target.value
        setSelectedDevices(typeof value === 'string' ? value.split(',') as DeviceType[] : value)
    }

    return (
        <FormControl sx={{ minWidth, p: 0.5 }}>
            <InputLabel id='device-multiselect-label'>{label}</InputLabel>
            <Select
                multiple
                size='small'
                value={selectedDevices}
                onChange={handleDevicesChange}
                label={label}
                labelId='device-multiselect-label'
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
    )
}

export default DeviceMultiSelect
