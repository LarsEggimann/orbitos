import { Box, Stack } from '@mui/material'
import { createFileRoute } from '@tanstack/react-router'
import Electrometer from '~/components/electrometer/electrometer'

export const Route = createFileRoute(
  '/_pathlessLayout/electrometer/$deviceId1/and/$deviceId2',
)({
  component: RouteComponent,
})

function RouteComponent() {
  const { deviceId1, deviceId2 } = Route.useParams()
  return (
    <Stack
      direction="row"
      sx={{
        width: '100%',
        height: '100%',
        gap: 1,
      }}>

      <Electrometer deviceId={parseInt(deviceId1)} />

      <Electrometer deviceId={parseInt(deviceId2)} />

    </Stack>

  )
}
