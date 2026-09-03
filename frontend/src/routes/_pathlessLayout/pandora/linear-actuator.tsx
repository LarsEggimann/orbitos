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
import PandoraLinearActuator from '~/components/pandora/PandoraLinearActuator'

export const Route = createFileRoute('/_pathlessLayout/pandora/linear-actuator')({
    component: RouteComponent,
})


function RouteComponent() {
    return <PandoraLinearActuator />
}

