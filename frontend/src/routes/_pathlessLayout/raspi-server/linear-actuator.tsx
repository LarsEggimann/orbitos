import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { createFileRoute } from '@tanstack/react-router'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import {
    Raspi as RaspiService,
    type BaseResponse,
    type RaspiGetBusStatusResponse,
    type RaspiState,
    type RaspiSettings
} from '~/generated'
import { useConfig } from '~/provider/ConfigProvider'
import { useDeviceWebSocket } from '~/utils/webSocketHook'

export const Route = createFileRoute('/_pathlessLayout/raspi-server/linear-actuator')({
    component: RouteComponent,
})

function RouteComponent() {
    const { API_WEBSOCKET_URL } = useConfig()
    const deviceName = 'raspi-server'

    const { state, settings, connected } = useDeviceWebSocket<
        RaspiState,
        {},
        RaspiSettings
    >({
        url: `${API_WEBSOCKET_URL}/raspi/ws`,
        fetchInitialState: async () =>
            (await RaspiService.raspiGetState()).data!,
        fetchInitialSettings: async () =>
            (await RaspiService.raspiGetSettings()).data!,
        dataAppendFunction: (_) => { },
    })


    return <>
        <Stack direction='row' sx={{ alignItems: 'center', gap: 2, mt: 5 }}>
            <ExecQueryButton
                onClick={async () => {
                    return await RaspiService.raspiExtendLinAct({
                        path: {lin_act_id: 1},
                    })
                }}
            >
                Extend Linear Actuator 1
            </ExecQueryButton>
            <ExecQueryButton
                onClick={async () => {
                    return await RaspiService.raspiRetractLinAct({
                        path: {lin_act_id: 1},
                    })
                }}
            >
                Retract Linear Actuator 1
            </ExecQueryButton>
        </Stack>

        {JSON.stringify(state, null, 2)}        
            <Stack direction='row' sx={{ alignItems: 'center', gap: 2, mt: 2 }}>
                <Typography variant="body1" sx={{ fontWeight: 'bold' }} color='text.primary'>
                    Linear Actuator 1 State: {state?.bus_status?.[1]?.status || 'Unknown'}
                </Typography>
            </Stack>

    </>
}
