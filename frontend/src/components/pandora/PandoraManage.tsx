import React from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Divider from '@mui/material/Divider'
import Stack from '@mui/material/Stack'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'

import {
    Pandora as PandoraService,
    type PandoraState,
    type PandoraSettings,
    type PandoraDataResponse
} from '~/generated'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import { useDeviceWebSocket } from '~/utils/webSocketHook'
import { useConfig } from '~/provider/ConfigProvider'
import ServerStatusIndicator from '~/components/ui/ServerStatusIndicator'


const PandoraManage: React.FC = () => {
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
        dataAppendFunction: (_) => { },
    })

    return (
        <Box sx={{ p: 1 }}>

            <Stack
                direction='row'
                sx={{ alignItems: 'center', justifyContent: 'space-between', mb: 3 }}
            >
                <Typography variant='h5'>PANDORA Server Management</Typography>
            </Stack>
            <Divider sx={{ my: 2, mt: 0 }} />
            
            <Card sx={{ mb: 3, border: '1px solid', borderColor: 'divider' }}>
                <CardContent>
                    <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                        📡 Server Status & Documentation
                    </Typography>
                    <ServerStatusIndicator 
                        url="http://pandora-server:8000/docs"
                        checkInterval={10000}
                    />
                </CardContent>
            </Card>
            <Divider sx={{ my: 2, mt: 0 }} />


            <Card sx={{ p: 2, mb: 2, width: '100%' }}>
                <Typography variant="h6" sx={{  }}>
                    PANDORA Server Controls
                </Typography>
                <Typography variant="body2" sx={{ mb: 1, pb: 0.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                    Start and Stop the PANDORA Server Application on the Raspberry Pi
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
                    Settings (not yet editable via UI)
                </Typography>
                <pre style={{ margin: 0, fontSize: '0.85rem', overflowX: 'auto' }}>
                    {JSON.stringify(settings, null, 2)}
                </pre>
            </Card>
        </Box>
    )
}

export default PandoraManage