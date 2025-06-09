import { createFileRoute } from '@tanstack/react-router'
import TimeSeriesChart from '~/components/plots/PlotlyPlot'
import Button from '~/components/ui/Button'
import { ElectrometerService, ElectrometerId } from '~/generated'
import { useDeviceWebSocket } from '~/utils/webSocketHook'
import { DeviceStateDisplay, DeviceSettingsDisplay } from '~/components/ui/DeviceDisplays'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Divider from '@mui/material/Divider'
import { DeviceSettingsForm } from '~/components/ui/DeviceSettingsForm'
import Tabs from '@mui/material/Tabs'
import Tab from '@mui/material/Tab'
import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import debounce from 'lodash.debounce'
import type { AxiosResponse, AxiosError } from 'axios';

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

  const [tab, setTab] = useState(0)
  const [localSettings, setLocalSettings] = useState(settings)

  // Sync localSettings with websocket settings
  useEffect(() => {
    setLocalSettings(settings)
  }, [settings])

  // Debounced update for settings (waits 1.5s after last change before sending)
  const debouncedUpdate = useRef(
    debounce(
      (
        key: string,
        value: any,
        resolve: (value: AxiosResponse<any> | AxiosError<any> | void) => void,
        reject: (reason?: any) => void
      ) => {
        ElectrometerService.electrometerSetElectrometerSettings({
          path: { device_id: deviceIdFull },
          body: { [key]: value }
        })
          .then(resolve)
          .catch(reject);
      },
      200 // 200ms debounce time
    )
  ).current;

  const handleSettingChange = useCallback(
    (key: string, value: any): Promise<AxiosResponse<any> | AxiosError<any> | void> => {
      setLocalSettings(prev => {
        if (!prev) return { device_id: deviceIdFull, [key]: value };
        return { ...prev, [key]: value };
      });
      return new Promise((resolve, reject) => {
        debouncedUpdate(key, value, resolve, reject);
      });
    },
    [debouncedUpdate, deviceIdFull]
  )

  // Settings keys for tabs
  const triggerKeys = ['trigger_count', 'trigger_time_interval', 'trigger_delay']
  const continuousKeys = ['aperture_integration_time', 'aperture_auto', 'current_range', 'current_range_auto', 'current_range_auto_upper_limit', 'current_range_auto_lower_limit']

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
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Continuous Measurement" />
        <Tab label="Trigger Measurement" />
      </Tabs>
      {tab === 0 && (
        <Box>
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
          </Box>
          <DeviceSettingsForm
            settings={Object.fromEntries(Object.entries(localSettings || {}).filter(([k]) => continuousKeys.includes(k)))}
            onChange={handleSettingChange}
          />
        </Box>
      )}
      {tab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
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
          <DeviceSettingsForm
            settings={Object.fromEntries(Object.entries(localSettings || {}).filter(([k]) => triggerKeys.includes(k)))}
            onChange={handleSettingChange}
          />
        </Box>
      )}
      <Divider sx={{ my: 2 }} />
      <DeviceStateDisplay state={state} />
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
