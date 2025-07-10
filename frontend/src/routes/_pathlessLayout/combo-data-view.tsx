import ComboDataView from '@/components/combo-data-view/combo-data-view'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_pathlessLayout/combo-data-view')({
  component: RouteComponent,
})

function RouteComponent() {
  return <ComboDataView />
}
