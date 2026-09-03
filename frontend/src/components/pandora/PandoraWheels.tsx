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

const PandoraWheels: React.FC = () => {
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
                {/* Left Side: Dynamic list of 4 Wheels with live state routing */}
                <Box sx={{ flex: 1, width: '100%' }}>
                    {[0, 1, 2, 3].map((id) => {
                        // Extract individual wheel updates from state mapping dictionary keys securely
                        const wheelData = state?.wheels ? (state.wheels as any)[id] : undefined

                        return (
                            <PandoraWheelControl 
                                key={id} 
                                wheelId={id} 
                                wheelState={wheelData} 
                            />
                        )
                    })}
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
                        Crude Live State JSON
                    </Typography>
                    <pre style={{ margin: 0, fontSize: '0.85rem', overflowX: 'auto' }}>
                        {JSON.stringify(state, null, 2)}
                    </pre>
                </Card>
            </Box>

        </Box>
    )
}

export default PandoraWheels