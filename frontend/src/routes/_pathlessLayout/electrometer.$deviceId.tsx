import { useQuery } from '@tanstack/react-query'
import { createFileRoute, useParams } from '@tanstack/react-router'
import { ElectrometerState, ElectrometerService, ElectrometerId } from '~/generated'
import { useDeviceWebSocket } from '~/utils/webSocketHook'

export const Route = createFileRoute('/_pathlessLayout/electrometer/$deviceId')({
  component: RouteComponent,
})

function RouteComponent() {
  const { deviceId } = Route.useParams()
  const deviceIdFull = `electrometer_${deviceId}` as ElectrometerId
  const deviceIdPathArg = { path: { device_id: deviceIdFull } }

  var { state, data, settings, connected } = useDeviceWebSocket({
    url: `${import.meta.env.VITE_ORBITOS_API_WEBSOCKET_BASE_URL}/${deviceIdFull}`,
    fetchInitialState: async () => (await ElectrometerService.electrometerGetElectrometerState(deviceIdPathArg)).data!,
    fetchInitialData: async () =>  (await ElectrometerService.electrometerGetCurrentData(deviceIdPathArg)).data!,
    fetchInitialSettings: async () => (await ElectrometerService.electrometerGetElectrometerSettings(deviceIdPathArg)).data!,
  })

  return (
    <div>
      <h2>Live State via WebSocket {connected ? '🟢' : '🔴'}</h2>
      <pre>{JSON.stringify(state, null, 2)}</pre>

      <h3>Live Data</h3>
      <pre>{JSON.stringify(data, null, 2)}</pre>

      <h3>Settings</h3>
      <pre>{JSON.stringify(settings, null, 2)}</pre>
    </div>
  )
}
