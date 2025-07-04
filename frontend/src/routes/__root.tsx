import {
  Outlet,
  createRootRoute
} from '@tanstack/react-router'
import { DefaultCatchBoundary } from '~/components/DefaultCatchBoundary'
import { NotFound } from '~/components/NotFound'

export const Route = createRootRoute({
  errorComponent: (props) => {
    return (
        <DefaultCatchBoundary {...props} />
    )
  },
  notFoundComponent: () => <NotFound />,
  component: RootComponent,
})

function RootComponent() {
  return (
    <>
        <Outlet />
    </>
  )
}

