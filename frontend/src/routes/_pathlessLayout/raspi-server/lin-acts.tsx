import Stack from '@mui/material/Stack'
import { createFileRoute } from '@tanstack/react-router'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import {
    Raspi as RaspiService,
    type BaseResponse,
    type RaspiGetBusStatusResponse,
    type RaspiSettings
} from '~/generated'
import { useConfig } from '~/provider/ConfigProvider'
import { useDeviceWebSocket } from '~/utils/webSocketHook'

export const Route = createFileRoute('/_pathlessLayout/raspi-server/lin-acts')({
    component: RouteComponent,
})

function RouteComponent() {
    const { API_WEBSOCKET_URL } = useConfig()
    const deviceName = 'raspi-server'

    const { state, settings, connected } = useDeviceWebSocket<
        RaspiGetBusStatusResponse,
        {},
        RaspiSettings
    >({
        url: `${API_WEBSOCKET_URL}/raspi/ws`,
        fetchInitialState: async () =>
            (await RaspiService.raspiGetBusStatus()).data!,
        fetchInitialSettings: async () =>
            (await RaspiService.raspiGetSettings()).data!,
        dataAppendFunction: (_) => { },
    })


    return <>
        <Stack direction='row' sx={{ alignItems: 'center', gap: 2, mt: 5 }}>
            <ExecQueryButton
                onClick={async () => {
                    return await RaspiService.raspiExtractLinAct({
                        path: {lin_act_id: 1},
                    })
                }}
            >
                Extract Linear Actuator 1
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
    </>
}
