import { createFileRoute } from '@tanstack/react-router'
import TimeSeriesChart from '~/components/plots/PlotlyPlot'
import Button from '~/components/ui/Button'
import { ElectrometerService, ElectrometerId } from '~/generated'
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
    dataAppendFunction: (prevData, newData) => {
      if (!prevData) return newData
      return {
        device_id: prevData.device_id,
        time: [...prevData.time, ...newData.time],
        current: [...prevData.current, ...newData.current],
      }
    }
  })


  return (
    <div>
      <Button
        onClick={async () => {
          return await ElectrometerService.electrometerConnectToElectrometer({
            path: {
              device_id: deviceIdFull,
              ip: '192.168.113.72'
            }
          })
        }}
      >
        Connect to Electrometer {deviceId}
      </Button>
      <h2>Live State via WebSocket {connected ? '🟢' : '🔴'}</h2>
      <pre>{JSON.stringify(state, null, 2)}</pre>
      <h3>Settings</h3>
      <pre>{JSON.stringify(settings, null, 2)}</pre>
      <TimeSeriesChart
        xData={data?.time ?? []}
        yData={data?.current ?? []}
        height={500}
        title='Electrometer 1'
        xAxisLabel='Time'
        yAxisLabel='Current [A]'
        hoverTemplate='<b>Time:</b> %{customdata[0]}<br><b>Current:</b> %{customdata[1]} A<extra></extra>'
      />
    </div>
  )
}
