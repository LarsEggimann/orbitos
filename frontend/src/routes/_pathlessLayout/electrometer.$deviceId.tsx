import React, { useMemo } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import TimeSeriesChart from '~/components/plots/PlotlyPlot'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import { ElectrometerService, ElectrometerName, BaseState, ElectrometerDataResponse, ElectrometerState, ElectrometerSettings } from '~/generated'
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
import Card from '@mui/material/Card'

export const Route = createFileRoute('/_pathlessLayout/electrometer/$deviceId')({
  component: RouteComponent,
})

function RouteComponent() {
  const deviceId = parseInt(Route.useParams().deviceId)
  const deviceName = `electrometer_${deviceId}` as ElectrometerName
  const deviceIdPathArg = { path: { device_id: deviceId } }

  const [startDate, setStartDate] = React.useState(null as Date | null)
  const [endDate, setEndDate] = React.useState(null as Date | null)
  const [datesLoaded, setDatesLoaded] = useState(false);

  // persist date range in localStorage using deviceIdFull as key
  useEffect(() => {
    const savedStart = localStorage.getItem(`${deviceName}_startDate`);
    const savedEnd = localStorage.getItem(`${deviceName}_endDate`);
    if (savedStart) {
      setStartDate(new Date(savedStart));
    } else {
      // Default to 24 hours ago if no start date is saved
      setStartDate(new Date(Date.now() - 24 * 60 * 60 * 1000)); // 24 hours ago
    }
    if (savedEnd) setEndDate(new Date(savedEnd));
    setDatesLoaded(true);
  }, [deviceName]);

  useEffect(() => {
    if (startDate) localStorage.setItem(`${deviceName}_startDate`, startDate.toISOString());
    if (endDate) {
      localStorage.setItem(`${deviceName}_endDate`, endDate.toISOString());
    } else { // if endDate is null, clear it from localStorage, this allows to reset the end date
      localStorage.removeItem(`${deviceName}_endDate`);
    }
  }, [startDate, endDate, deviceName]);


  const [data, setData] = useState<ElectrometerDataResponse | undefined>(undefined)

  useQuery({
    queryKey: [deviceName, startDate, endDate],
    queryFn: async () => {
      const response = await ElectrometerService.electrometerGetCurrentData({
        ...deviceIdPathArg,
        query: {
          start: startDate?.toISOString(),
          end: endDate?.toISOString(),
        }
      })
      console.log('startDate:', startDate, 'endDate:', endDate)
      setData(response.data)
      console.log(response)
      return response.data
    },
    refetchOnWindowFocus: false,
    enabled: datesLoaded,
  })


  var { state, settings, connected } = useDeviceWebSocket<ElectrometerState, ElectrometerDataResponse, ElectrometerSettings>({
    url: `${import.meta.env.VITE_ORBITOS_API_WEBSOCKET_BASE_URL}/electrometer/ws/${deviceId}`,
    fetchInitialState: async () => (await ElectrometerService.electrometerGetElectrometerState(deviceIdPathArg)).data!,
    fetchInitialSettings: async () => (await ElectrometerService.electrometerGetElectrometerSettings(deviceIdPathArg)).data!,
    dataAppendFunction: (newData) => {
      setData(prevData => {
        if (!prevData) return newData
        return {
          device_name: prevData.device_name,
          timestamp: prevData.timestamp.concat(newData.timestamp),
          current: prevData.current.concat(newData.current),
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
          path: { device_id: deviceId },
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
        if (!prev) return { device_id: deviceId, [key]: value };
        return { ...prev, [key]: value };
      });
      return new Promise((resolve, reject) => {
        debouncedUpdate(key, value, resolve, reject);
      });
    },
    [debouncedUpdate, deviceId]
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
  const defaultIp = deviceId === 1 ? '192.168.113.72' : deviceId === 2 ? '192.168.113.73' : ipOptions[0].label;
  const [ip, setIp] = useState(defaultIp);


  // TODO: move this to utils
  function trapezoidIntegration(y: number[], x: number[]): number {
    if (y.length !== x.length) {
      throw new Error("y and x arrays must be the same length");
    }

    let integral = 0;
    for (let i = 0; i < y.length - 1; i++) {
      const dx = x[i + 1] - x[i];
      const avgY = 0.5 * (y[i + 1] + y[i]);
      integral += dx * avgY;
    }

    return integral;
  }
  const integratedCharge = useMemo(() => {
    if (!data?.current || !data?.timestamp) return null;
    try {
      return trapezoidIntegration(data.current, data.timestamp);
    } catch {
      return null;
    }
  }, [data?.current, data?.timestamp]);


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
              path: { device_id: deviceId, ip: ip }
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
        xData={data?.timestamp ?? []}
        yData={data?.current ?? []}
        height={500}
        xAxisLabel='Time'
        yAxisLabel='Current [A]'
        hoverTemplate='<b>Time:</b> %{customdata[0]}<br><b>Current:</b> %{customdata[1]} A<extra></extra>'
      />

      <Card sx={{ flexGrow: 1, my: 1, p: 2 }}>
        <Typography variant="h6" gutterBottom>Data Information</Typography>
        <Typography>Number of Datapoints lodaded: {data?.current.length}</Typography>
        <Typography>
          Total Duration: {data?.timestamp ? ((data?.timestamp[data.timestamp.length - 1] - data.timestamp[0]) / 60).toFixed(2) : "N/A"} minutes
        </Typography>
        <Typography>
          Integrated Charge: {integratedCharge
            ? integratedCharge.toExponential(3)
            : "N/A"} C
        </Typography>

      </Card>

      <DeviceStateDisplay state={state as BaseState} />


        <Box sx={{ m: 2 }}>
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

          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', m: 2 }}>
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
      <Divider sx={{ my: 2 }} />

    </Box>
  )
}
