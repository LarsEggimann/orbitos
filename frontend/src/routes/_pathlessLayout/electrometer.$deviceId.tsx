import { createFileRoute } from '@tanstack/react-router'
import Electrometer from '~/components/electrometer/electrometer'

export const Route = createFileRoute('/_pathlessLayout/electrometer/$deviceId')(
  {
    component: RouteComponent,
  },
)

function RouteComponent() {
  const deviceId = parseInt(Route.useParams().deviceId)

  return <Electrometer deviceId={deviceId} />
}
