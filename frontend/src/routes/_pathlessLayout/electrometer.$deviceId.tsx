import { createFileRoute } from '@tanstack/react-router'
import TimeSeriesChart from '~/components/plots/PlotlyPlot'
import Button from '~/components/ui/Button'
import { ElectrometerService, ElectrometerId } from '~/generated'
import { useDeviceWebSocket } from '~/utils/webSocketHook'
import { DeviceStateDisplay, DeviceSettingsDisplay } from '~/components/ui/DeviceDisplays'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Divider from '@mui/material/Divider'

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
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 2 }}>
      <Typography variant="h4" gutterBottom>Electrometer {deviceId}</Typography>
      <Typography variant="subtitle1" gutterBottom>Live State via WebSocket {connected ? '🟢' : '🔴'}</Typography>
      <Divider sx={{ my: 2 }} />
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
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
          Connect
        </Button>
        <Button
          onClick={async () => {
            return await ElectrometerService.electrometerDisconnectElectrometer({
              path: { device_id: deviceIdFull }
            })
          }}
        >
          Disconnect
        </Button>
        <Button
          onClick={async () => {
            return await ElectrometerService.electrometerResetElectrometer()
          }}
        >
          Reset All
        </Button>
        <Button
          onClick={async () => {
            return await ElectrometerService.electrometerResetElectrometerError({
              path: { device_id: deviceIdFull }
            })
          }}
        >
          Reset Error
        </Button>
      </Box>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
        <Button
          onClick={async () => {
            return await ElectrometerService.electrometerStartContinuousMeasurement({
              path: { device_id: deviceIdFull }
            })
          }}
        >
          Start Continuous
        </Button>
        <Button
          onClick={async () => {
            return await ElectrometerService.electrometerStopContinuousMeasurement({
              path: { device_id: deviceIdFull }
            })
          }}
        >
          Stop Continuous
        </Button>
        <Button
          onClick={async () => {
            return await ElectrometerService.electrometerInitializeTriggerBasedMeasurement({
              path: { device_id: deviceIdFull }
            })
          }}
        >
          Init Trigger
        </Button>
        <Button
          onClick={async () => {
            return await ElectrometerService.electrometerStartTriggerBasedMeasurement({
              path: { device_id: deviceIdFull }
            })
          }}
        >
          Start Trigger
        </Button>
      </Box>
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
        <Button
          onClick={async () => {
            return await ElectrometerService.electrometerGetElectrometerState({
              path: { device_id: deviceIdFull }
            })
          }}
        >
          Get State
        </Button>
        <Button
          onClick={async () => {
            return await ElectrometerService.electrometerGetElectrometerSettings({
              path: { device_id: deviceIdFull }
            })
          }}
        >
          Get Settings
        </Button>
        <Button
          onClick={async () => {
            // Set a valid setting: e.g., set current_range_auto to 'ON' (as a demo)
            return await ElectrometerService.electrometerSetElectrometerState({
              path: { device_id: deviceIdFull },
              body: { current_range_auto: 'ON' }
            })
          }}
        >
          Set Auto Range ON
        </Button>
        <Button
          onClick={async () => {
            return await ElectrometerService.electrometerGetCurrentData({
              path: { device_id: deviceIdFull }
            })
          }}
        >
          Get Data
        </Button>
      </Box>
      <Divider sx={{ my: 2 }} />
      <DeviceStateDisplay state={state} />
      <DeviceSettingsDisplay settings={settings} />
      <TimeSeriesChart
        xData={data?.time ?? []}
        yData={data?.current ?? []}
        height={400}
        title={`Electrometer ${deviceId}`}
        xAxisLabel='Time'
        yAxisLabel='Current [A]'
        hoverTemplate='<b>Time:</b> %{customdata[0]}<br><b>Current:</b> %{customdata[1]} A<extra></extra>'
      />
    </Box>
  )
}
