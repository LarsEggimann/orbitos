import { createFileRoute } from '@tanstack/react-router'
import PandoraManage from '~/components/pandora/PandoraManage'

export const Route = createFileRoute('/_pathlessLayout/pandora/manage')({
  component: RouteComponent,
})

function RouteComponent() {
  return <PandoraManage />
}
