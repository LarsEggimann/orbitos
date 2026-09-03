import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Chip from '@mui/material/Chip'
import Divider from '@mui/material/Divider'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { createFileRoute } from '@tanstack/react-router'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import { useConfig } from '~/provider/ConfigProvider'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useDeviceWebSocket } from '~/utils/webSocketHook'
import type { AxiosError, AxiosResponse } from 'axios'
import { useSnackbarContext } from '~/provider/SnackbarProvider'
import DirtyTextField from '~/components/ui/DirtyTextField'

import {
    Pandora as PandoraService,
    type PandoraState,
    type PandoraSettings,
    type PandoraDataResponse,
    type RelayState,
} from '~/generated'

function Actuator({
    id,
    relay_state,
    onExtend,
    onRetract,
}: {
    id: number
    relay_state?: RelayState
    onExtend: () => Promise<AxiosResponse<any> | AxiosError<any> | void>
    onRetract: () => Promise<AxiosResponse<any> | AxiosError<any> | void>
}) {
    const actuatorY =
        relay_state?.is_on
            ? '65%' // down = in beam
            : '0%'  // up = out of beam

    const actuatorColor =
        relay_state?.is_on
            ? 'warning.main'
            : 'success.main'

    const label =
        relay_state?.is_on === false
            ? 'Out of Beam'
            : relay_state?.is_on === true
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

const PandoraLinearActuator: React.FC = () => {
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

      const { openSnackbar } = useSnackbarContext()
    

      const setSettingsQuery = useMutation({
        mutationFn: async (settings: Record<string, any>) => {
        return await PandoraService.pandoraSetPandoraSettings({
            body: settings,
        })
        },
        onSuccess: (result) => {
        console.log(result)
        const status = result.status

        if (status != 200) {
            let msg = 'An error occurred while changing setting'

            if (result.request?.statusText) {
            msg = result.request.statusText
            }

            // look for result.error and then result.error.detail
            if (result.error?.detail) {
            msg = msg + ': ' + result.error.detail
            }

            openSnackbar(msg, 'error')
            throw new Error('Error setting settings: ' + msg)
        } else {
            let msg = 'Settings updated successfully'
            if (result.data?.message) {
            msg = result.data.message
            }

            openSnackbar(msg, 'success')
        }
        },
        onError: (error: AxiosError) => {
        console.error(error)
        },
    })

    function makeSettingApplyHandler(key: string) {
        return async (value: string) => {
        console.log(`Applying setting ${key} with value:`, value)
        return new Promise<boolean>((resolve) => {
            setSettingsQuery.mutate(
            { [key]: value },
            {
                onSuccess: () => resolve(true),
                onError: () => resolve(false),
            },
            )
        })
        }
    }

    

    return (
        <Box sx={{ p: 1 }}>
            <Stack
                direction="row"
                sx={{ alignItems: 'center', justifyContent: 'space-between' }}
            >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="h5">PANDORA - Linear Actuator Control - </Typography>
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
                        {Object.entries(state?.relays ?? {}).map(([id, relay]) => {
                            const relayId = Number(id)
                            const descriptionKey =
                                `pandora_relay_${relayId}_description` as keyof PandoraSettings

                            return (
                                <Stack
                                    key={id}
                                    sx={{ alignItems: 'center' }}
                                    spacing={1}
                                >
                                    <DirtyTextField
                                        label="Description"
                                        value={settings?.[descriptionKey] ?? ''}
                                        onApply={makeSettingApplyHandler(descriptionKey)}
                                    />

                                    <Actuator
                                        id={relayId}
                                        relay_state={relay}
                                        onExtend={() =>
                                            PandoraService.pandoraTurnOnRelay({
                                                path: { relay_id: relayId },
                                            })
                                        }
                                        onRetract={() =>
                                            PandoraService.pandoraTurnOffRelay({
                                                path: { relay_id: relayId },
                                            })
                                        }
                                    />
                                </Stack>
                            )
                        })}             
                    </Box>
                </CardContent>
            </Card>
        </Box>
    )
}

export default PandoraLinearActuator