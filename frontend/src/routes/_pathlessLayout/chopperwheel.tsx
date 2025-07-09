import Chopperwheel from '@/components/chopperwheel/chopperwheel'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_pathlessLayout/chopperwheel')({
  component: RouteComponent,
})

function RouteComponent() {
  return <Chopperwheel />
}
