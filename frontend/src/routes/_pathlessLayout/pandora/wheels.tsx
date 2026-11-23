import { createFileRoute } from '@tanstack/react-router'
import PandoraWheels from '~/components/pandora/PandoraWheels'

export const Route = createFileRoute('/_pathlessLayout/pandora/wheels')({
  component: RouteComponent,
})

function RouteComponent() {
  return <PandoraWheels />
}
