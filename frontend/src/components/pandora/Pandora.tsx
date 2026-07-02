import React from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Divider from '@mui/material/Divider'
import Stack from '@mui/material/Stack'
import Card from '@mui/material/Card'

import {
    Pandora as PandoraService,
    type PandoraState,
    type PandoraSettings,
    type PandoraDataResponse
} from '~/generated'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import { useDeviceWebSocket } from '~/utils/webSocketHook'
import { useConfig } from '~/provider/ConfigProvider'
import PandoraWheelControl from './PandoraWheelControl'

const Pandora: React.FC = () => {
    const { API_WEBSOCKET_URL } = useConfig()

    const { state, settings, connected } = useDeviceWebSocket<
        PandoraState,
        PandoraDataResponse,
        PandoraSettings
    >({
        url: `${API_WEBSOCKET_URL}/pandora/ws`,
        fetchInitialState: async () =>
            (await PandoraService.pandoraGetState()).data!,
        fetchInitialSettings: async () =>
            (await PandoraService.pandoraGetSettings()).data!,
        dataAppendFunction: (newData) => { },
    })


    // start stop pandora server



    return (
        <Box sx={{ p: 1 }}>

            <Stack
                direction="row"
                sx={{ alignItems: 'center', justifyContent: 'space-between' }}
            >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="h5">PANDORA's Box - </Typography>
                    <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center' }}>
                        {state?.connection_status === 'connected' ? '🟢' : '🔴'}
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="subtitle1">
                        Live State via WebSocket {connected ? '🟢' : '🔴'}
                    </Typography>
                </Box>
            </Stack>
            <Divider sx={{ my: 2, mt: 0 }} />

            {/* Main Layout Container (Split View) */}
            <Box
                sx={{
                    display: 'flex',
                    gap: 3,
                    flexDirection: { xs: 'column', md: 'row' },
                    alignItems: 'flex-start',
                    mb: 3
                }}
            >
                {/* Left Side: Dynamic list of 4 Wheels */}
                <Box sx={{ flex: 1, width: '100%' }}>
                    {[0, 1, 2, 3].map((id) => (
                        <PandoraWheelControl key={id} wheelId={id} />
                    ))}
                </Box>

                {/* Right Side: Live State JSON (Sticky pinned) */}
                <Card
                    sx={{
                        p: 2,
                        minWidth: { xs: '100%', md: 350 },
                        maxWidth: { md: 550 },
                        flexShrink: 0,
                        position: { md: 'sticky' },
                        top: { md: 16 },
                        maxHeight: { md: 'calc(100vh - 100px)' },
                        overflowY: 'auto'
                    }}
                >
                    <Typography variant="h6" color="primary" sx={{ mb: 1, pb: 0.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                        Live State
                    </Typography>
                    <pre style={{ margin: 0, fontSize: '0.85rem', overflowX: 'auto' }}>
                        {JSON.stringify(state, null, 2)}
                    </pre>
                </Card>
            </Box>

            <Card sx={{ p: 2, mb: 2, width: '100%' }}>
                <Typography variant="h6" sx={{ mb: 1, pb: 0.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                    PANDORA Server Controls
                </Typography>
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap', gap: 1, ml: { sm: 'auto' } }}>
                    <ExecQueryButton
                        onClick={async () => {
                            return await PandoraService.pandoraStartServer()
                        }}
                        size="small"
                        tooltip={`Start PANDORA server - this will launch the pandora server app on the raspberry`}
                    >
                        Start PANDORA Server
                    </ExecQueryButton>

                    <ExecQueryButton
                        onClick={async () => {
                            return await PandoraService.pandoraStopServer()
                        }}
                        size="small"
                        tooltip={`Stop PANDORA server - this will stop the pandora server app on the raspberry`}
                    >
                        Stop PANDORA Server
                    </ExecQueryButton>
                    <ExecQueryButton
                        onClick={async () => {
                            return await PandoraService.pandoraServerHealthCheck()
                        }}
                        size="small"
                        tooltip={`Check PANDORA server health - this will verify the status of the pandora server app on the raspberry`}
                    >
                        Check PANDORA Server Health
                    </ExecQueryButton>
                </Stack>
            </Card>

            {/* Bottom Row: Settings Dashboard */}
            <Card sx={{ p: 2, mb: 2, width: '100%' }}>
                <Typography variant="h6" sx={{ mb: 1, pb: 0.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                    Settings
                </Typography>
                <pre style={{ margin: 0, fontSize: '0.85rem', overflowX: 'auto' }}>
                    {JSON.stringify(settings, null, 2)}
                </pre>
            </Card>
        </Box>
    )
}

export default Pandora