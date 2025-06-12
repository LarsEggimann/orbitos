import React from 'react'
import { createFileRoute } from '@tanstack/react-router'
import TimeSeriesChart from '~/components/plots/PlotlyPlot'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import { ElectrometerService, ElectrometerId, BaseState, CurrentDataResponse, ElectrometerState, ElectrometerSettings } from '~/generated'
import { useDeviceWebSocket } from '~/utils/webSocketHook'
import { DeviceStateDisplay, DeviceSettingsDisplay } from '~/components/ui/DeviceStateDisplay'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Divider from '@mui/material/Divider'
import { DeviceSettingsForm } from '~/components/ui/DeviceSettingsForm'
import Tabs from '@mui/material/Tabs'
import Tab from '@mui/material/Tab'
import { useState, useEffect, useCallback, useRef } from 'react'
import debounce from 'lodash.debounce'
import type { AxiosResponse, AxiosError } from 'axios';
import IpAutocomplete from '~/components/ui/IpAutocomplete';
import Stack from '@mui/material/Stack'
import { useQuery } from '@tanstack/react-query'
import DateRangeSelect from '~/components/ui/DataRangeSelection'

export const Route = createFileRoute('/_pathlessLayout/electrometer/$deviceId')({
  component: RouteComponent,
})

function RouteComponent() {
  const { deviceId } = Route.useParams()
  const deviceIdFull = `electrometer_${deviceId}` as ElectrometerId
  const deviceIdPathArg = { path: { device_id: deviceIdFull } }

  const [startDate, setStartDate] = React.useState(new Date(new Date().setHours(0, 0, 0, 0)) as Date | null)
  const [endDate, setEndDate] = React.useState(null as Date | null)

  const [data, setData] = useState<CurrentDataResponse | undefined>(undefined)

  useQuery({
    queryKey: ['electrometerData', deviceIdFull, startDate, endDate],
    queryFn: async () => {
      const response = await ElectrometerService.electrometerGetCurrentData({
        ...deviceIdPathArg,
        query: {
          start: startDate?.toISOString(),
          end: endDate?.toISOString(),
        }
      })
      setData(response.data)
    },
    refetchOnWindowFocus: false,
  })


  var { state, settings, connected } = useDeviceWebSocket<ElectrometerState, CurrentDataResponse, ElectrometerSettings>({
    url: `${import.meta.env.VITE_ORBITOS_API_WEBSOCKET_BASE_URL}/${deviceIdFull}`,
    fetchInitialState: async () => (await ElectrometerService.electrometerGetElectrometerState(deviceIdPathArg)).data!,
    fetchInitialSettings: async () => (await ElectrometerService.electrometerGetElectrometerSettings(deviceIdPathArg)).data!,
    dataAppendFunction: (newData) => {
      setData(prevData => {
        if (!prevData) return newData
        return {
          device_id: prevData.device_id,
          time: [...prevData.time, ...newData.time],
          current: [...prevData.current, ...newData.current],
        }
      })
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
      200 // debounce time
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

  // IP Dropdown State
  const ipOptions = [
    { label: '192.168.113.72' },
    { label: '192.168.113.73' }
  ];
  // Default IP logic: 72 for electrometer 1, 73 for electrometer 2
  const defaultIp = deviceId === '1' ? '192.168.113.72' : deviceId === '2' ? '192.168.113.73' : ipOptions[0].label;
  const [ip, setIp] = useState(defaultIp);

  return (
    <Box sx={{ p: 2, borderRadius: 1, bgcolor: 'background.paper', boxShadow: 1 }}>
      <Stack
        direction="row"
        sx={{ alignItems: 'center', justifyContent: 'space-between' }}
      >
        <Typography variant="h4">Electrometer {deviceId}</Typography>
        <Typography variant="subtitle1">Live State via WebSocket {connected ? '🟢' : '🔴'}</Typography>
      </Stack>
      <Divider sx={{ my: 2, mt: 0 }} />

      <Stack
        direction="row"
        sx={{ alignItems: 'center', gap: 2, my: 2 }}>
        <IpAutocomplete
          value={ip}
          onChange={setIp}
          options={ipOptions}
          label="Electrometer IP"
          sx={{ minWidth: 220 }}
        />
        <ExecQueryButton
          onClick={async () => {
            return await ElectrometerService.electrometerConnectToElectrometer({
              path: { device_id: deviceIdFull, ip: ip }
            })
          }}
        >
          Connect
        </ExecQueryButton>
        <ExecQueryButton
          onClick={async () => {
            return await ElectrometerService.electrometerDisconnectElectrometer(deviceIdPathArg)
          }}
          color='warning'
        >
          Disconnect
        </ExecQueryButton>
        <Box flexGrow={1}></Box>
        <ExecQueryButton
          onClick={async () => {
            return await ElectrometerService.electrometerResetElectrometerError(deviceIdPathArg)
          }}

        >
          Reset Error
        </ExecQueryButton>
      </Stack>

      <DateRangeSelect
        startState={[startDate, setStartDate]}
        endState={[endDate, setEndDate]}
      >
        
      </DateRangeSelect>



      <TimeSeriesChart
        xData={data?.time ?? []}
        yData={data?.current ?? []}
        height={400}
        title={`Electrometer ${deviceId}`}
        xAxisLabel='Time'
        yAxisLabel='Current [A]'
        hoverTemplate='<b>Time:</b> %{customdata[0]}<br><b>Current:</b> %{customdata[1]} A<extra></extra>'
      />

      <DeviceStateDisplay state={state as BaseState} />

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Continuous Measurement" />
        <Tab label="Trigger Measurement" />
      </Tabs>
      {tab === 0 && (
        <Box>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
            <ExecQueryButton
              onClick={async () => {
                return await ElectrometerService.electrometerStartContinuousMeasurement(deviceIdPathArg)
              }}
            >
              Start Continuous
            </ExecQueryButton>
            <ExecQueryButton
              onClick={async () => {
                return await ElectrometerService.electrometerStopContinuousMeasurement(deviceIdPathArg)
              }}
            >
              Stop Continuous
            </ExecQueryButton>
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
            <ExecQueryButton
              onClick={async () => {
                return await ElectrometerService.electrometerInitializeTriggerBasedMeasurement(deviceIdPathArg)
              }}
            >
              Init Trigger
            </ExecQueryButton>
            <ExecQueryButton
              onClick={async () => {
                return await ElectrometerService.electrometerStartTriggerBasedMeasurement(deviceIdPathArg)
              }}
            >
              Start Trigger
            </ExecQueryButton>
          </Box>
          <DeviceSettingsForm
            settings={Object.fromEntries(Object.entries(localSettings || {}).filter(([k]) => triggerKeys.includes(k)))}
            onChange={handleSettingChange}
          />
        </Box>
      )}
      <Divider sx={{ my: 2 }} />

    </Box>
  )
}
