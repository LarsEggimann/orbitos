import { Outlet, createFileRoute } from '@tanstack/react-router'
import Layout from '~/components/ui/Layout'

export const Route = createFileRoute('/_pathlessLayout')({
  component: PathlessLayoutComponent,
})

function PathlessLayoutComponent() {
  return (
    <div>
      <Layout>
        <Outlet />
      </Layout>
    </div>
  )
}
