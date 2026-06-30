import { createFileRoute } from '@tanstack/react-router'
import Pandora from '~/components/pandora/pandora'

export const Route = createFileRoute('/_pathlessLayout/pandora')({
  component: RouteComponent,
})

function RouteComponent() {
  return <Pandora />
}
