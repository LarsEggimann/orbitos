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
import { useState, useEffect, useCallback, useRef } from 'react'
import debounce from 'lodash.debounce'
import type { AxiosResponse, AxiosError } from 'axios';
import IpAutocomplete from '~/components/ui/IpAutocomplete';
import Stack from '@mui/material/Stack'
import { useMutation, useQuery } from '@tanstack/react-query'
import DateRangeSelect from '~/components/ui/DataRangeSelection'
import Card from '@mui/material/Card'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableRow from '@mui/material/TableRow'
import TableCell from '@mui/material/TableCell'
import TextField from '@mui/material/TextField'
import DirtyTextField, { DirtyTextFieldHandle } from '~/components/ui/DirtyTextField'
import Button from '@mui/material/Button'
import Snackbar from '~/components/ui/Snackbar'
import { BaseResponse } from '~/generated'

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

  const dataQuery = useQuery({
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

  const [conversionFactor, setConversionFactor] = useState(1); // Default conversion factor
  useEffect(() => {
    // Load conversion factor from localStorage if available
    const savedFactor = localStorage.getItem(`${deviceName}_conversionFactor`);
    if (savedFactor) {
      setConversionFactor(parseFloat(savedFactor));
    }
  }, [deviceName]);
  useEffect(() => {
    // Save conversion factor to localStorage whenever it changes
    localStorage.setItem(`${deviceName}_conversionFactor`, conversionFactor.toString());
  }, [conversionFactor, deviceName]);

  const field1Ref = useRef<DirtyTextFieldHandle>(null);

  const applyAll = () => {
    field1Ref.current?.tryApply();
  };

  const [snackbar, setSnackbar] = React.useState<{ open: boolean, msg: string, severity: 'success' | 'error' }>({ open: false, msg: '', severity: 'success' });

  const openSnackbar = (msg: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, msg, severity });
  };

  const setSettingsQuery = useMutation({
    mutationFn: async (settings: Record<string, any>) => {
      return await ElectrometerService.electrometerSetElectrometerSettings({
        path: { device_id: deviceId },
        body: settings
      });
    },
    onSuccess: (result) => {

      console.log(result);
      const status = result.status

      if (status != 200) {

        let msg = 'An error occurred while changing setting';

        if (result.request && result.request.statusText) {
          msg = result.request.statusText;
        }

        // look for result.error and then result.error.detail
        if (result.error && result.error.detail) {
          msg = msg + ': ' + result.error.detail;
        }

        openSnackbar(msg, 'error');
        throw new Error('Error setting settings: ' + msg);

      } else {
        let msg = 'Settings updated successfully';
        if (result.data && result.data.message) {
          msg = result.data.message;
        }

        openSnackbar(msg, 'success');
      }
    },
    onError: (error: AxiosError) => {
      console.error(error);
    }
  });

  function makeSettingApplyHandler(key: string) {
  return async (value: string) => {
    console.log(`Applying setting ${key} with value:`, value);
    return new Promise<boolean>((resolve) => {
      setSettingsQuery.mutate(
        { [key]: value },
        {
          onSuccess: () => resolve(true),
          onError: () => resolve(false),
        }
      );
    });
  };
}





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
        dataQuery={dataQuery}
        height={500}
        xAxisLabel='Time'
        yAxisLabel='Current [A]'
        hoverTemplate='<b>Time:</b> %{customdata[0]}<br><b>Current:</b> %{customdata[1]} A<extra></extra>'
      />

      <Card sx={{ flexGrow: 1, my: 1, p: 2 }}>
        <Typography variant="h6">Plot Data Information</Typography>
        <Table sx={{ minWidth: 300 }}>
          <TableBody>
            <TableRow>
              <TableCell sx={{ border: 0, pl: 0, pr: 2, width: '30%' }}>
                <Typography>Number of Datapoints loaded:</Typography>
              </TableCell>
              <TableCell sx={{ border: 0, pl: 0 }}>
                <Typography>
                  {data?.current.length}
                </Typography>
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell sx={{ border: 0, pl: 0, pr: 2 }}>
                <Typography>Loaded Timeframe:</Typography>
              </TableCell>
              <TableCell sx={{ border: 0, pl: 0 }}>
                <Typography>
                  {data?.timestamp ? ((data?.timestamp[data.timestamp.length - 1] - data.timestamp[0]) / 60).toFixed(2) : "N/A"} minutes
                </Typography>
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell sx={{ border: 0, pl: 0, pr: 2 }}>
                <Typography>Integrated Charge:</Typography>
              </TableCell>
              <TableCell sx={{ border: 0, pl: 0 }}>
                <Typography>
                  {integratedCharge
                    ? integratedCharge.toExponential(6)
                    : "N/A"} C
                </Typography>
              </TableCell>
              <TableCell sx={{ border: 0, pl: 0, pr: 2 }}>
                <TextField
                  variant='standard'
                  size='small'
                  label={'Conversion Factor [Gy/C]'}
                  value={conversionFactor}
                  onChange={(e) => {
                    const value = parseFloat(e.target.value);
                    if (!isNaN(value)) {
                      setConversionFactor(value);
                    }
                  }}
                  type={'number'}
                />
              </TableCell>
              <TableCell sx={{ border: 0, pl: 0 }}>
                <Typography>
                  {integratedCharge
                    ? (integratedCharge * conversionFactor).toExponential(6)
                    : "N/A"} Gy
                </Typography>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
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

        <DirtyTextField
          label={'Auto Current Range Upper Limit [A]'}
          value={settings?.current_range_auto_upper_limit ?? ''}
          onApply={makeSettingApplyHandler('current_range_auto_upper_limit')}
        />

        <DirtyTextField
          label={'Auto Current Range [ON/OFF]'}
          onOff={true}
          value={settings?.current_range_auto ?? ''}
          onApply={makeSettingApplyHandler('current_range_auto')}
        />

        <Button
          onClick={applyAll}>
          Apply All Settings

        </Button>



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

      <Snackbar
        openState={[snackbar.open, (open) => setSnackbar(prev => ({ ...prev, open: open as boolean }))]}
        alertProps={{
          message: snackbar.msg,
          severity: snackbar.severity
        }}

      />

    </Box>
  )
}
