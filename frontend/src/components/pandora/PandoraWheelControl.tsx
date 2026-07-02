import React, { useState } from 'react'
import Box from '@mui/material/Box'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import ZoomOutMapIcon from '@mui/icons-material/ZoomOutMap'
import SearchIcon from '@mui/icons-material/Search'
import DoNotDisturbIcon from '@mui/icons-material/DoNotDisturb'

import ExecQueryButton from '~/components/ui/ExecQueryButton'
import { Pandora as PandoraService } from '~/generated'

interface PandoraWheelControlProps {
    wheelId: number
}

const PandoraWheelControl: React.FC<PandoraWheelControlProps> = ({ wheelId }) => {
    const [targetPosition, setTargetPosition] = useState<number | string>('')

    const presetPositions = Array.from({ length: 8 }, (_, i) => ({
        label: i,
        angle: i * 45
    }))

    return (
        <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1, mb: 2, bgcolor: 'background.paper' }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'medium' }}>
                Wheel #{wheelId}
            </Typography>

            <Stack spacing={2}>
                {/* Main Control Row */}
                <Stack direction="row" sx={{ flexWrap: 'wrap', gap: 2, alignItems: 'center', justifyContent: 'space-between' }}>
                    
                    {/* Left Side: Target Position Controls */}
                    <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
                        <TextField
                            variant="outlined"
                            size="small"
                            label="Target Position [°]"
                            value={targetPosition}
                            onChange={(e) => setTargetPosition(e.target.value)}
                            type="number"
                            sx={{ width: 220 }} // Made wider as requested
                        />

                        <ExecQueryButton
                            onClick={async () => {
                                if (targetPosition === '') return
                                return await PandoraService.pandoraGoToPosition({
                                    path: { wheel_id: wheelId, angle_deg: Number(targetPosition) },
                                })
                            }}
                            size="small"
                            startIcon={<ZoomOutMapIcon />}
                            tooltip={`Move wheel #${wheelId} to ${targetPosition}°`}
                            disabled={targetPosition === ''}
                        >
                            Move To Position
                        </ExecQueryButton>
                    </Stack>

                    {/* Right Side: Reference Search Controls */}
                    <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap', gap: 1, ml: { sm: 'auto' } }}>
                        <ExecQueryButton
                            onClick={async () => {
                                return await PandoraService.pandoraStartReferenceSearch({
                                    path: { wheel_id: wheelId },
                                })
                            }}
                            size="small"
                            startIcon={<SearchIcon />}
                            tooltip={`Start reference search for wheel #${wheelId}`}
                        >
                            Start Ref. Search
                        </ExecQueryButton>

                        <ExecQueryButton
                            onClick={async () => {
                                return await PandoraService.pandoraStopReferenceSearch({
                                    path: { wheel_id: wheelId },
                                })
                            }}
                            size="small"
                            startIcon={<DoNotDisturbIcon />}
                            tooltip={`Stop reference search for wheel #${wheelId}`}
                        >
                            Stop Ref. Search
                        </ExecQueryButton>
                    </Stack>
                </Stack>

                {/* Preset Position Buttons (0-7) */}
                <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                    {presetPositions.map((preset) => (
                        <ExecQueryButton
                            key={preset.label}
                            onClick={async () => {
                                return await PandoraService.pandoraGoToPosition({
                                    path: { wheel_id: wheelId, angle_deg: preset.angle },
                                })
                            }}
                            size="small"
                            tooltip={`Move wheel #${wheelId} to position ${preset.label} (${preset.angle}°)`}
                        >
                            Pos {preset.label} ({preset.angle}°)
                        </ExecQueryButton>
                    ))}
                </Stack>
            </Stack>
        </Box>
    )
}

export default PandoraWheelControl