import Stack from '@mui/material/Stack'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Divider from '@mui/material/Divider'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import { createFileRoute } from '@tanstack/react-router'
import { Raspi as RaspiService } from '~/generated'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import ServerStatusIndicator from '~/components/ui/ServerStatusIndicator'

export const Route = createFileRoute('/_pathlessLayout/raspi-server/manage')({
    component: RouteComponent,
})

function RouteComponent() {
    return (
        <Box sx={{ bgcolor: 'background.paper' }}>
            <Stack
                direction='row'
                sx={{ alignItems: 'center', justifyContent: 'space-between', mb: 3 }}
            >
                <Typography variant='h5'>Raspi Server Management</Typography>
            </Stack>
            <Divider sx={{ my: 2, mt: 0 }} />
            
            <Card sx={{ mb: 3, border: '1px solid', borderColor: 'divider' }}>
                <CardContent>
                    <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                        📡 Server Status & Documentation
                    </Typography>
                    <ServerStatusIndicator 
                        url="http://raspi-server:8000/docs"
                        checkInterval={10000}
                    />
                </CardContent>
            </Card>

            <Card sx={{ border: '1px solid', borderColor: 'divider' }}>
                <CardContent>
                    <Typography variant="h6" sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                        🎛️ Server Controls
                    </Typography>
                    <Stack 
                        direction='row' 
                        sx={{ 
                            alignItems: 'center', 
                            gap: 2, 
                            flexWrap: 'wrap',
                            justifyContent: 'flex-start'
                        }}
                    >
                        <ExecQueryButton
                            onClick={async () => {
                                return await RaspiService.raspiServerHealthCheck()
                            }}
                            color="primary"
                        >
                            Health Check Raspi Server
                        </ExecQueryButton>
                        <ExecQueryButton
                            onClick={async () => {
                                return await RaspiService.raspiStartServer()
                            }}
                            color="primary"
                        >
                            Start Raspi Server
                        </ExecQueryButton>
                        <ExecQueryButton
                            onClick={async () => {
                                return await RaspiService.raspiStopServer()
                            }}
                            color="warning"
                        >
                            Stop Raspi Server
                        </ExecQueryButton>
                    </Stack>
                </CardContent>
            </Card>
        </Box>
    )
}
