import { createFileRoute } from '@tanstack/react-router'
import XyStages from '~/components/xy-stages/xy-stages'

export const Route = createFileRoute('/_pathlessLayout/stages')({
  component: RouteComponent,
})

function RouteComponent() {
  return <XyStages />
}
