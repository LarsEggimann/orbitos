import { useQuery } from '@tanstack/react-query'
import { createFileRoute, useParams } from '@tanstack/react-router'
import { ElectrometerState, ElectrometerService, ElectrometerId } from '~/generated'
import { useWebSocket } from '~/utils/webSocketHook'

export const Route = createFileRoute('/_pathlessLayout/electrometer/$deviceId')({
  component: RouteComponent,
})

function RouteComponent() {
  const { deviceId } = Route.useParams()
  const deviceIdFull = `electrometer_${deviceId}` as ElectrometerId
  const deviceIdPathArg = { path: { device_id: deviceIdFull } }

  var { state, data, settings, connected } = useWebSocket({
    url: `${import.meta.env.VITE_ORBITOS_API_WEBSOCKET_BASE_URL}/${deviceIdFull}`,
  })

  const myQuery = useQuery<ElectrometerState>({
    queryKey: ['electrometerState'],
    queryFn: async () => {
      const response = await ElectrometerService.electrometerGetElectrometerState(deviceIdPathArg)
      if (!response.data) {
        throw new Error(`Failed to fetch electrometer state: ${response.status} ${response.error}`)
      }
      return response.data
    }
  })

  return (
    <div>
      <h2>Electrometer State (Initial Load)</h2>
      {myQuery.isLoading && <p>Loading...</p>}
      {myQuery.isError && <p>Error: {myQuery.error.message}</p>}
      {myQuery.isSuccess && (
        <pre>{JSON.stringify(myQuery.data, null, 2)}</pre>
      )}

      <h2>Live State via WebSocket {connected ? '🟢' : '🔴'}</h2>
      <pre>{JSON.stringify(state, null, 2)}</pre>

      <h3>Live Data</h3>
      <pre>{JSON.stringify(data, null, 2)}</pre>

      <h3>Settings</h3>
      <pre>{JSON.stringify(settings, null, 2)}</pre>
    </div>
  )
}
