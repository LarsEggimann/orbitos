import { createFileRoute } from '@tanstack/react-router'
import Pandora from '~/components/pandora/Pandora'

export const Route = createFileRoute('/_pathlessLayout/pandora')({
  component: RouteComponent,
})

function RouteComponent() {
  return <Pandora />
}
