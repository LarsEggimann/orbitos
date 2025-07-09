import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_pathlessLayout/stages')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/_pathlessLayout/stages"!</div>
}
