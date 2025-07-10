import React, { useState } from 'react'
import { Box, Stack, TextField, Typography, Dialog, DialogTitle, DialogContent, DialogActions, Button } from '@mui/material'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import { XyStages as XyStagesService } from '~/generated'
import PrestyledButton from '../ui/PrestyledButton'

interface AxisControlProps {
    axis: 'x-axis' | 'y-axis'
    value: number
    onChange: (value: number) => void
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

            <Stack direction='row' spacing={1} sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}>
                <TextField
                    variant='outlined'
                    size='small'
                    label={`${axisLabel} Input [mm]`}
                    value={value}
                    onChange={(e) => {
                        const val = e.target.value
                        if (val === '' || !isNaN(Number(val))) {
                            onChange(Number(val))
                        }
                    }}
                    type='number'
                    sx={{}}
                />

                <ExecQueryButton
                    onClick={async () => {
                        return await XyStagesService.xyStagesMoveAxisByMm({
                            path: { axis, mm: value },
                        })
                    }}
                    disabled={!isConnected}
                    size='small'
                >
                    Move By
                </ExecQueryButton>

                <ExecQueryButton
                    onClick={async () => {
                        return await XyStagesService.xyStagesMoveAxisToPosition({
                            path: { axis, position: value },
                        })
                    }}
                    disabled={!isConnected}
                    size='small'
                >
                    Move To
                </ExecQueryButton>
            </Stack>

            <PrestyledButton
                onClick={() => setZeroConfirmOpen(true)}
                disabled={!isConnected}
                color='warning'
                size='small'
                fullWidth
                variant='outlined'
            >
                Set Current Position to Zero
            </PrestyledButton>

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
