import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Chip from '@mui/material/Chip'
import Divider from '@mui/material/Divider'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { createFileRoute } from '@tanstack/react-router'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import { Raspi as RaspiService } from '~/generated'
import type { LinActStatus, RaspiSettings, RaspiState } from '~/generated'
import { useConfig } from '~/provider/ConfigProvider'
import { useDeviceWebSocket } from '~/utils/webSocketHook'
import type { AxiosError, AxiosResponse } from 'axios'

export const Route = createFileRoute('/_pathlessLayout/raspi-server/linear-actuator')({
    component: RouteComponent,
})


function Actuator({
    id,
    status,
    onExtend,
    onRetract,
}: {
    id: number
    status?: LinActStatus
    onExtend: () => Promise<AxiosResponse<any> | AxiosError<any> | void>
    onRetract: () => Promise<AxiosResponse<any> | AxiosError<any> | void>
}) {
    const actuatorY =
        status === 'retracted'
            ? '0%' // up = out of beam
            : status === 'extended'
                ? '65%' // down = in beam
                : '35%'

    const actuatorColor =
        status === 'retracted'
            ? 'success.main'
            : status === 'extended'
                ? 'error.main'
                : 'text.disabled'

    const label =
        status === 'retracted'
            ? 'Out of Beam'
            : status === 'extended'
                ? 'In Beam'
                : 'Unknown'

    return (
        <Stack sx={{ alignItems: 'center' }} spacing={1}>
            <Chip
                size="small"
                color={
                    'default'
                }
                label={`#${id} - ${label}`}
            />
            <Box
                sx={{
                    position: 'relative',
                    width: 50,
                    height: 160,
                    border: '2px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    background: 'linear-gradient(180deg, rgba(0,0,0,0.04), transparent)',
                    overflow: 'hidden',
                }}
            >
                <Box
                    sx={{
                        position: 'absolute',
                        top: actuatorY,
                        left: 5,
                        right: 5,
                        height: 40,
                        borderRadius: 1,
                        bgcolor: actuatorColor,
                        transition: 'top 0.5s ease-in-out',
                        boxShadow: 3,
                    }}
                />
            </Box>
            <Stack direction="row" spacing={1}>
                <ExecQueryButton
                    color="warning"
                    onClick={onExtend}
                >
                    Extend
                </ExecQueryButton>
                <ExecQueryButton
                    color="success"
                    onClick={onRetract}
                >
                    Retract
                </ExecQueryButton>
            </Stack>
        </Stack>
    )
}

function RouteComponent() {
    const { API_WEBSOCKET_URL } = useConfig()

    const { state, connected } = useDeviceWebSocket<
        RaspiState,
        {},
        RaspiSettings
    >({
        url: `${API_WEBSOCKET_URL}/raspi/ws`,
        fetchInitialState: async () => (await RaspiService.raspiGetState()).data!,
        fetchInitialSettings: async () =>
            (await RaspiService.raspiGetSettings()).data!,
        dataAppendFunction: (_) => { },
    })

    const actuators = [1, 2, 3, 4].map((i) => {
        const act = state?.bus_status?.[i]
        return {
            id: i,
            status: (act?.status as LinActStatus) ?? 'unknown',
        }
    })

    return (
        <Box sx={{ p: 3 }}>
            <Stack
                direction="row"
                sx={{ alignItems: 'center', justifyContent: 'space-between' }}
            >
                <Typography variant="h5">Linear Actuators</Typography>
                <Typography variant="subtitle1">
                    Live State via WebSocket {connected ? '🟢' : '🔴'}
                </Typography>
            </Stack>

            <Divider sx={{ my: 2 }} />

            <Card sx={{ border: '1px solid', borderColor: 'divider' }}>
                <CardContent>
                    <Box
                        sx={{
                            position: 'relative',
                            display: 'flex',
                            justifyContent: 'space-around',
                            alignItems: 'center',
                            height: 300,
                            overflow: 'visible',
                        }}
                    >
                        {/* Beam line */}
                        <Box
                            sx={{
                                position: 'absolute',
                                top: '65%',
                                left: 0,
                                right: 0,
                                height: 4,
                                bgcolor: 'primary.main',
                                opacity: 0.5,
                            }}
                        />
                        <Typography
                            variant="body2"
                            sx={{
                                position: 'absolute',
                                left: 8,
                                top: 'calc(65% - 20px)',
                                color: 'text.secondary',
                            }}
                        >
                            Beam →
                        </Typography>

                        {/* Actuators */}
                        {actuators.map((a) => (
                            <Actuator
                                key={a.id}
                                id={a.id}
                                status={a.status}
                                onExtend={async () =>
                                    RaspiService.raspiExtendLinAct({ path: { lin_act_id: a.id } })
                                }
                                onRetract={async () =>
                                    RaspiService.raspiRetractLinAct({ path: { lin_act_id: a.id } })
                                }
                            />
                        ))}
                    </Box>
                </CardContent>
            </Card>
        </Box>
    )
}

