import { createFileRoute } from '@tanstack/react-router'
import PandoraLinearActuator from '~/components/pandora/PandoraLinearActuator'

export const Route = createFileRoute('/_pathlessLayout/pandora/linear-actuator')({
    component: RouteComponent,
})

function RouteComponent() {
    return <PandoraLinearActuator />
}

