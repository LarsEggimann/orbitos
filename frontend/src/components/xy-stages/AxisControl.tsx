import React, { useState } from 'react'
import { Box, Stack, TextField, Typography, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import ZoomOutMapIcon from '@mui/icons-material/ZoomOutMap';
import ZoomInMapIcon from '@mui/icons-material/ZoomInMap';
import ScaleIcon from '@mui/icons-material/Scale';
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import { XyStages as XyStagesService } from '~/generated'
import PrestyledButton from '../ui/PrestyledButton'

interface AxisControlProps {
    axis: 'x-axis' | 'y-axis'
    value: number | string
    onChange: (value: number | string) => void
    connectionStatus?: string
}

export const AxisControl: React.FC<AxisControlProps> = ({
    axis,
    value,
    onChange,
    connectionStatus,
}) => {
    const axisLabel = axis === 'x-axis' ? 'X' : 'Y'
    const isConnected = connectionStatus === 'connected'
    const [zeroConfirmOpen, setZeroConfirmOpen] = useState(false)

    const handleZeroPosition = async () => {
        const result = await XyStagesService.xyStagesSetAxisCurrentPositionToZero({
            path: { axis },
        })
        setZeroConfirmOpen(false)
        return result
    }

    return (
        <Box sx={{ flex: 1, p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
            <Typography variant='body1' sx={{ mb: 2 }}>{axisLabel} Axis Control</Typography>

            <Stack direction='row' sx={{ mb: 2, flexWrap: 'wrap', gap: 1, justifyContent: 'space-between' }}>
                <Stack direction='row' spacing={1} sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}>

                    <TextField
                        variant='outlined'
                        size='small'
                        label={`${axisLabel} Input [mm]`}
                        value={value}
                        onChange={(e) => {
                            const val = e.target.value
                            onChange(val)
                        }}
                        type='number'
                        sx={{}}
                    />

                    <ExecQueryButton
                        onClick={async () => {
                            return await XyStagesService.xyStagesMoveAxisByMm({
                                path: { axis, mm: Number(value) },
                            })
                        }}
                        disabled={!isConnected}
                        size='small'
                        startIcon={<ZoomOutMapIcon />}
                        tooltip='Move BY the specified distance relative to the current position'
                    >
                        Move By
                    </ExecQueryButton>

                    <ExecQueryButton
                        onClick={async () => {
                            return await XyStagesService.xyStagesMoveAxisToPosition({
                                path: { axis, position: Number(value) },
                            })
                        }}
                        disabled={!isConnected}
                        size='small'
                        startIcon={<ZoomInMapIcon />}
                        tooltip='Move TO the specified position'
                    >
                        Move To
                    </ExecQueryButton>
                </Stack>

                <Stack direction='row' spacing={1} sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}>

                    <PrestyledButton
                        onClick={() => setZeroConfirmOpen(true)}
                        disabled={!isConnected}
                        color='warning'
                        size='small'
                        startIcon={<ScaleIcon />}
                        tooltip='Set the current axis position to zero'
                    >
                        Set Zero
                    </PrestyledButton>
                </Stack>
            </Stack>


            <Dialog open={zeroConfirmOpen} onClose={() => setZeroConfirmOpen(false)}>
                <DialogTitle>Confirm Zero Position</DialogTitle>
                <DialogContent>
                    <Typography>
                        Are you sure you want to set the current {axisLabel} axis position to zero?
                        This will reset the position reference point and cannot be undone.
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <PrestyledButton onClick={() => setZeroConfirmOpen(false)}>
                        Cancel
                    </PrestyledButton>
                    <ExecQueryButton
                        onClick={handleZeroPosition}
                        color='warning'
                    >
                        Confirm
                    </ExecQueryButton>
                </DialogActions>
            </Dialog>
        </Box>
    )
}
