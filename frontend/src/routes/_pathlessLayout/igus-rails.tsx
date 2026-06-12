import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_pathlessLayout/igus-rails')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello From LARS!!!"!</div>
}
