import React, { useState } from 'react'
import Box from '@mui/material/Box'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Chip from '@mui/material/Chip'
import ZoomOutMapIcon from '@mui/icons-material/ZoomOutMap'
import SearchIcon from '@mui/icons-material/Search'
import DoNotDisturbIcon from '@mui/icons-material/DoNotDisturb'

import ExecQueryButton from '~/components/ui/ExecQueryButton'
import { Pandora as PandoraService } from '~/generated'

interface PandoraWheelControlProps {
    wheelId: number
    wheelState?: {
        status: string
        position: number | null
        velocity: number | null
    }
}

const PandoraWheelControl: React.FC<PandoraWheelControlProps> = ({ wheelId, wheelState }) => {
    const [targetPosition, setTargetPosition] = useState<number | string>('')

    const presetPositions = Array.from({ length: 8 }, (_, i) => ({
        label: i,
        angle: i * 45
    }))

    // determine status badge color dynamically
    const getStatusColor = (status?: string) => {
        if (!status) return 'error' // returns theme red if status is missing or not fetched
        
        switch (status.toLowerCase()) {
            case 'idle': return 'success'
            case 'moving': return 'warning'
            case 'unknown': return 'warning'
            case 'error': return 'error'
            default: return 'default'
        }
    }

    return (
        <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1, mb: 2, bgcolor: 'background.paper' }}>
            
            {/* Header: Centered 3-Column Grid Layout */}
            <Box 
                sx={{ 
                    display: 'grid', 
                    gridTemplateColumns: { xs: '1fr', sm: '1fr auto 1fr' }, 
                    alignItems: 'center', 
                    mb: 2, 
                    gap: 2 
                }}
            >
                {/* Left Column: Title & Status */}
                <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
                    <Typography variant="h6" sx={{ fontWeight: 'medium' }}>
                        Wheel #{wheelId}
                    </Typography>
                    <Chip 
                        label={wheelState?.status ? wheelState.status : 'not fetched'} 
                        size="small" 
                        color={getStatusColor(wheelState?.status)}
                        variant="outlined"
                    />
                </Stack>

                {/* Middle Column: Telemetry (Centered) */}
                <Stack direction="row" spacing={4} sx={{ justifyContent: 'center', alignItems: 'center' }}>
                    <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="caption" color="text.secondary">POSITION</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 'bold', fontFamily: 'monospace' }}>
                            {wheelState?.position !== null && wheelState?.position !== undefined ? `${wheelState.position}°` : '—'}
                        </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="caption" color="text.secondary">VELOCITY</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 'bold', fontFamily: 'monospace' }}>
                            {wheelState?.velocity !== null && wheelState?.velocity !== undefined ? `${wheelState.velocity} rps` : '—'}
                        </Typography>
                    </Box>
                </Stack>

                {/* Right Column: Balanced Spacer for desktop viewports */}
                <Box sx={{ display: { xs: 'none', sm: 'block' } }} />
            </Box>

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
                            sx={{ width: 220 }}
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