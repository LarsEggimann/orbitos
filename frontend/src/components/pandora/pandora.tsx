import React, { useMemo, useState, useEffect } from 'react'
import type { AxiosError } from 'axios'
import { useMutation, useQuery } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Divider from '@mui/material/Divider'
import Stack from '@mui/material/Stack'
import Card from '@mui/material/Card'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableRow from '@mui/material/TableRow'
import TableCell from '@mui/material/TableCell'
import TextField from '@mui/material/TextField'
import ZoomOutMapIcon from '@mui/icons-material/ZoomOutMap';
import ZoomInMapIcon from '@mui/icons-material/ZoomInMap';
import DoNotDisturbIcon from '@mui/icons-material/DoNotDisturb';
import SearchIcon from '@mui/icons-material/Search';
import Switch from '@mui/material/Switch'
import FormControlLabel from '@mui/material/FormControlLabel'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import HourglassBottomIcon from '@mui/icons-material/HourglassBottom';
import FlashOnIcon from '@mui/icons-material/FlashOn';
import FlashOffIcon from '@mui/icons-material/FlashOff';
import StopIcon from '@mui/icons-material/Stop';
import EMPlot from '~/components/electrometer/EMPlot'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import ConnectionButtons from '~/components/ui/ConnectionButtons'
import {
    Pandora as PandoraService,
    type PandoraState,
    type PandoraSettings,
    type PandoraDataResponse
} from '~/generated'
import { useDeviceWebSocket } from '~/utils/webSocketHook'
import IpAutocomplete from '~/components/electrometer/IpAutocomplete'
import DateRangeSelect from '~/components/ui/DataRangeSelection'
import DirtyTextField from '~/components/ui/DirtyTextField'
import DownloadCSVButton from '~/components/ui/DownloadCSVButton'
import { useSnackbarContext } from '~/provider/SnackbarProvider'
import { trapezoidIntegration } from '~/utils/helpers'
import { useConfig } from '~/provider/ConfigProvider'


const Pandora: React.FC = () => {
    const { API_WEBSOCKET_URL } = useConfig()

    const [data, setData] = useState<PandoraDataResponse | undefined>(undefined)
    const { openSnackbar } = useSnackbarContext()

    const [wheelId, setWheelId] = useState<number | undefined>(undefined)
    const [targetPosition, setTargetPosition] = useState<number | undefined>(undefined)

    const { state, settings, connected } = useDeviceWebSocket<
        PandoraState,
        PandoraDataResponse,
        PandoraSettings
    >({
        url: `${API_WEBSOCKET_URL}/pandora/ws`,
        fetchInitialState: async () =>
            (
                await PandoraService.pandoraGetState()
            ).data!,
        fetchInitialSettings: async () =>
            (
                await PandoraService.pandoraGetSettings()
            ).data!,
        dataAppendFunction: (newData) => {

            // no data stream yet, i.e future for temp sensor

        },
    })

    return (
        <Box sx={{ bgcolor: 'background.paper' }}>
            <Stack
                direction='row'
                sx={{ alignItems: 'center', justifyContent: 'space-between' }}
            >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant='h5'>PANDORA's Box - </Typography>
                    <Typography
                        variant='subtitle1'
                        sx={{ display: 'flex', alignItems: 'center' }}
                    >
                        {state?.connection_status == 'connected' ? '🟢' : '🔴'}
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant='subtitle1'>
                        Live State via WebSocket {connected ? '🟢' : '🔴'}
                    </Typography>
                </Box>
            </Stack>
            <Divider sx={{ my: 2, mt: 0 }} />

            {/* <PandoraStateDisplay state={state as PandoraState} /> */}
            <Box sx={{ flex: 1, p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>

                <Stack direction='row' sx={{ mb: 2, flexWrap: 'wrap', gap: 1, justifyContent: 'space-between' }}>
                    <Stack direction='row' spacing={1} sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}>

                        <TextField
                            variant='outlined'
                            size='small'
                            label={`Wheel Id Input`}
                            value={wheelId}
                            onChange={(e) => {
                                const val = e.target.value
                                setWheelId(Number(val))
                            }}
                            type='number'
                            sx={{}}
                        />
                        <TextField
                            variant='outlined'
                            size='small'
                            label={`Wheel # ${wheelId} - Target Position [°]`}
                            value={targetPosition}
                            onChange={(e) => {
                                const val = e.target.value
                                setTargetPosition(Number(val))
                            }}
                            type='number'
                            sx={{}}
                        />


                        <ExecQueryButton
                            onClick={async () => {
                                return await PandoraService.pandoraGoToPosition({
                                    path: { wheel_id: Number(wheelId), angle_deg: Number(targetPosition) },
                                })
                            }}
                            // disabled={!isConnected}
                            size='small'
                            startIcon={<ZoomOutMapIcon />}
                            tooltip={`Move wheel #${wheelId} to target position ${targetPosition}°`}
                        >
                            Move To Position
                        </ExecQueryButton>

                        <ExecQueryButton
                            onClick={async () => {
                                return await PandoraService.pandoraStartReferenceSearch({
                                    path: { wheel_id: Number(wheelId) },
                                })
                            }}
                            // disabled={!isConnected}
                            size='small'
                            startIcon={<SearchIcon />}
                            tooltip={`Start reference search for wheel #${wheelId}`}
                        >
                            Start Reference Search
                        </ExecQueryButton>

                        <ExecQueryButton
                            onClick={async () => {
                                return await PandoraService.pandoraStopReferenceSearch({
                                    path: { wheel_id: Number(wheelId) },
                                })
                            }}
                            // disabled={!isConnected}
                            size='small'
                            startIcon={<DoNotDisturbIcon />}
                            tooltip={`Stop reference search for wheel #${wheelId}`}
                        >
                            Stop Reference Search
                        </ExecQueryButton>
                    </Stack>

                    <Stack direction='row' spacing={1} sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}>

                    </Stack>
                </Stack>

            </Box>

            {/* print the json of the state and settings for now, until we have a better UI */}
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Card sx={{ p: 2, flexGrow: 1, minWidth: 300 }}>
                    <Typography variant='h6'>State</Typography>
                    <pre>{JSON.stringify(state, null, 2)}</pre>
                </Card>
                <Card sx={{ p: 2, flexGrow: 1, minWidth: 300, maxWidth: 500 }}>
                    <Typography variant='h6'>Settings</Typography>
                    <pre>{JSON.stringify(settings, null, 2)}</pre>
                </Card>
            </Box>

        </Box>
    )
}

export default Pandora
