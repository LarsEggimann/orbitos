import { createFileRoute, Link } from '@tanstack/react-router'

export const Route = createFileRoute('/_pathlessLayout/')({
  component: Home,
})

function Home() {
  return (
    <div className='p-2'>
      <h3>This is ORBITOS v2!!!</h3>
      <Link to='/electrometer/$deviceId' params={{ deviceId: '1' }}>
        Go to Electrometer 1
      </Link>
      <br />
      <Link to='/electrometer/$deviceId' params={{ deviceId: '2' }}>
        Go to Electrometer 2
      </Link>
    </div>
  )
}
