import Stack from '@mui/material/Stack'
import { createFileRoute } from '@tanstack/react-router'
import { Raspi as RaspiService } from '~/generated'
import ExecQueryButton from '~/components/ui/ExecQueryButton'

export const Route = createFileRoute('/_pathlessLayout/raspi-server/manage')({
    component: RouteComponent,
})

function RouteComponent() {



    return <>
        <Stack direction='row' sx={{ alignItems: 'center', gap: 2, mt: 5 }}>
            <ExecQueryButton
                onClick={async () => {
                    return await RaspiService.raspiServerHealthCheck()
                }}
            >
                Health Check Raspi Server
            </ExecQueryButton>
            <ExecQueryButton
                onClick={async () => {
                    return await RaspiService.raspiStartServer()
                }}
            >
                Start Raspi Server
            </ExecQueryButton>
            <ExecQueryButton
                onClick={async () => {
                    return await RaspiService.raspiStopServer()
                }}
            >
                Stop Raspi Server
            </ExecQueryButton>
        </Stack>
    </>
}
