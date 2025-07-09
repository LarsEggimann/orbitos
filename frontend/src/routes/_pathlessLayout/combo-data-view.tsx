import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_pathlessLayout/combo-data-view')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/_pathlessLayout/combo-data-view"!</div>
}
