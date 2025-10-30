import React, { useMemo, useState, useEffect } from 'react'
import type { AxiosError } from 'axios'
import { useMutation, useQuery } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Divider from '@mui/material/Divider'
import Stack from '@mui/material/Stack'
import Card from '@mui/material/Card'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableRow from '@mui/material/TableRow'
import TableCell from '@mui/material/TableCell'
import TextField from '@mui/material/TextField'
import Switch from '@mui/material/Switch'
import FormControlLabel from '@mui/material/FormControlLabel'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import HourglassBottomIcon from '@mui/icons-material/HourglassBottom';
import FlashOnIcon from '@mui/icons-material/FlashOn';
import FlashOffIcon from '@mui/icons-material/FlashOff';
import StopIcon from '@mui/icons-material/Stop';
import TimeSeriesChart from '~/components/plots/TimeSeriesPlot'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import ConnectionButtons from '~/components/ui/ConnectionButtons'
import {
  Electrometer as ElectrometerService,
  type ElectrometerName,
  type ElectrometerDataResponse,
  type ElectrometerState,
  type ElectrometerSettings,
} from '~/generated'
import { useDeviceWebSocket } from '~/utils/webSocketHook'
import { ElectrometerStateDisplay } from '~/components/electrometer/ElectrometerStateDisplay'
import IpAutocomplete from '~/components/electrometer/IpAutocomplete'
import DateRangeSelect from '~/components/ui/DataRangeSelection'
import DirtyTextField from '~/components/ui/DirtyTextField'
import DownloadCSVButton from '~/components/ui/DownloadCSVButton'
import { useSnackbarContext } from '~/provider/SnackbarProvider'
import { trapezoidIntegration } from '~/utils/helpers'
import { useConfig } from '~/provider/ConfigProvider'

type ElectrometerProps = {
  deviceId: number
}

const Electrometer: React.FC<ElectrometerProps> = ({ deviceId }) => {
  const { API_WEBSOCKET_URL } = useConfig()
  const deviceName = `electrometer_${deviceId}` as ElectrometerName
  const deviceIdPathArg = { path: { device_id: deviceId } }

  const [startDate, setStartDate] = React.useState(null as Date | null)
  const [endDate, setEndDate] = React.useState(null as Date | null)
  const [datesLoaded, setDatesLoaded] = useState(false)

  // persist date range in localStorage using deviceIdFull as key
  useEffect(() => {
    const savedStart = localStorage.getItem(`${deviceName}_startDate`)
    const savedEnd = localStorage.getItem(`${deviceName}_endDate`)
    if (savedStart) {
      setStartDate(new Date(savedStart))
    } else {
      // Default to 12 hours ago if no start date is saved
      setStartDate(new Date(Date.now() - 12 * 60 * 60 * 1000)) // 12 hours ago
    }
    if (savedEnd) setEndDate(new Date(savedEnd))
    setDatesLoaded(true)
  }, [deviceName])

  useEffect(() => {
    try {
      if (startDate)
        localStorage.setItem(`${deviceName}_startDate`, startDate.toISOString())
      if (endDate) {
        localStorage.setItem(`${deviceName}_endDate`, endDate.toISOString())
      } else {
        // if endDate is null, clear it from localStorage, this allows to reset the end date
        localStorage.removeItem(`${deviceName}_endDate`)
      }
    } catch (error) {
      console.error('Error saving date range to localStorage:', error)
    }
  }, [startDate, endDate, deviceName])

  const [data, setData] = useState<ElectrometerDataResponse | undefined>(
    undefined,
  )

  // State for controlling data append
  const [dataAppendEnabled, setDataAppendEnabled] = useState<boolean>(() => {
    const saved = localStorage.getItem(`${deviceName}_dataAppendEnabled`)
    return saved ? JSON.parse(saved) : true // Default to enabled
  })

  useEffect(() => {
    localStorage.setItem(
      `${deviceName}_dataAppendEnabled`,
      JSON.stringify(dataAppendEnabled),
    )
  }, [dataAppendEnabled, deviceName])

  const dataQuery = useQuery({
    queryKey: [deviceName, startDate, endDate],
    queryFn: async () => {
      const response = await ElectrometerService.electrometerGetCurrentData({
        ...deviceIdPathArg,
        query: {
          start: startDate?.toISOString(),
          end: endDate?.toISOString(),
        },
      })
      setData(response.data)
      return response.data
    },
    refetchOnWindowFocus: true,
    enabled: datesLoaded,
  })

  const { state, settings, connected } = useDeviceWebSocket<
    ElectrometerState,
    ElectrometerDataResponse,
    ElectrometerSettings
  >({
    url: `${API_WEBSOCKET_URL}/electrometer/ws/${deviceId}`,
    fetchInitialState: async () =>
      (
        await ElectrometerService.electrometerGetElectrometerState(
          deviceIdPathArg,
        )
      ).data!,
    fetchInitialSettings: async () =>
      (
        await ElectrometerService.electrometerGetElectrometerSettings(
          deviceIdPathArg,
        )
      ).data!,
    dataAppendFunction: (newData) => {
      if (!dataAppendEnabled) return // Don't append if disabled
      
      setData((prevData) => {
        if (!prevData) return newData
        return {
          device_name: prevData.device_name,
          timestamp: prevData.timestamp.concat(newData.timestamp),
          current: prevData.current.concat(newData.current),
        }
      })
    },
  })

  // IP Dropdown State
  const ipOptions = [{ label: '192.168.113.72' }, { label: '192.168.113.73' }]

  const [ip, setIp] = useState('')
  useEffect(() => {
    // Default IP logic: 72 for electrometer 1, 73 for electrometer 2
    let defaultIp = ipOptions[0].label
    if (deviceId === 2) {
      defaultIp = ipOptions[1].label
    }
    // Set default IP based on deviceId when component mounts
    setIp(defaultIp)
  }, [deviceId])

  const integratedCharge = useMemo(() => {
    if (!data?.current || !data?.timestamp) return null
    try {
      return trapezoidIntegration(data.current, data.timestamp)
    } catch {
      return null
    }
  }, [data?.current, data?.timestamp])

  const [conversionFactor, setConversionFactor] = useState(1) // Default conversion factor
  useEffect(() => {
    // Load conversion factor from localStorage if available
    const savedFactor = localStorage.getItem(`${deviceName}_conversionFactor`)
    if (savedFactor) {
      setConversionFactor(parseFloat(savedFactor))
    }
  }, [deviceName])
  useEffect(() => {
    // Save conversion factor to localStorage whenever it changes
    localStorage.setItem(
      `${deviceName}_conversionFactor`,
      conversionFactor.toString(),
    )
  }, [conversionFactor, deviceName])

  // const field1Ref = useRef<DirtyTextFieldHandle>(null)

  const { openSnackbar } = useSnackbarContext()

  const setSettingsQuery = useMutation({
    mutationFn: async (settings: Record<string, any>) => {
      return await ElectrometerService.electrometerSetElectrometerSettings({
        path: { device_id: deviceId },
        body: settings,
      })
    },
    onSuccess: (result) => {
      console.log(result)
      const status = result.status

      if (status != 200) {
        let msg = 'An error occurred while changing setting'

        if (result.request?.statusText) {
          msg = result.request.statusText
        }

        // look for result.error and then result.error.detail
        if (result.error?.detail) {
          msg = msg + ': ' + result.error.detail
        }

        openSnackbar(msg, 'error')
        throw new Error('Error setting settings: ' + msg)
      } else {
        let msg = 'Settings updated successfully'
        if (result.data?.message) {
          msg = result.data.message
        }

        openSnackbar(msg, 'success')
      }
    },
    onError: (error: AxiosError) => {
      console.error(error)
    },
  })

  function makeSettingApplyHandler(key: string) {
    return async (value: string) => {
      console.log(`Applying setting ${key} with value:`, value)
      return new Promise<boolean>((resolve) => {
        setSettingsQuery.mutate(
          { [key]: value },
          {
            onSuccess: () => resolve(true),
            onError: () => resolve(false),
          },
        )
      })
    }
  }

  const [triggerCount, setTriggerCount] = useState(settings?.trigger_count || 0)
  useEffect(() => {
    setTriggerCount(Number(settings?.trigger_count) || 0)
  }, [settings?.trigger_count])

  const [triggerTime, setTriggerTime] = useState(
    settings?.trigger_time_interval || 0,
  )
  useEffect(() => {
    setTriggerTime(Number(settings?.trigger_time_interval) || 0)
  }, [settings?.trigger_time_interval])

  return (
    <Box sx={{ bgcolor: 'background.paper' }}>
      <Stack
        direction='row'
        sx={{ alignItems: 'center', justifyContent: 'space-between' }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant='h5'>Electrometer {deviceId} - </Typography>
          <Typography
            variant='subtitle1'
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            {state?.connection_status == 'connected' ? '🟢' : '🔴'}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControlLabel
            control={
              <Switch
                checked={dataAppendEnabled}
                onChange={(e) => setDataAppendEnabled(e.target.checked)}
                color="primary"
              />
            }
            label="Live Data Append"
            sx={{ mb: 0 }}
          />
          <Typography variant='subtitle1'>
            Live State via WebSocket {connected ? '🟢' : '🔴'}
          </Typography>
        </Box>
      </Stack>
      <Divider sx={{ my: 2, mt: 0 }} />

      <Stack direction='row' sx={{ alignItems: 'center', gap: 2, my: 2 }}>
        <IpAutocomplete
          value={ip}
          onChange={setIp}
          options={ipOptions}
          label='Electrometer IP'
          sx={{ minWidth: 220 }}
        />
        <ConnectionButtons
          connectionStatus={state?.connection_status}
          onConnect={async () => {
            return await ElectrometerService.electrometerConnectToElectrometer({
              path: { device_id: deviceId, ip: ip },
            })
          }}
          onDisconnect={async () => {
            return await ElectrometerService.electrometerDisconnectElectrometer(
              deviceIdPathArg,
            )
          }}
          showResetError={true}
          onResetError={async () => {
            return await ElectrometerService.electrometerResetElectrometerError(
              deviceIdPathArg,
            )
          }}
        />
      </Stack>

      <DateRangeSelect
        startState={[startDate, setStartDate]}
        endState={[endDate, setEndDate]}
      ></DateRangeSelect>

      <ElectrometerStateDisplay state={state as ElectrometerState} />

      <TimeSeriesChart
        xData={data?.timestamp ?? []}
        yData={data?.current ?? []}
        dataQuery={dataQuery}
        height={500}
        xAxisLabel='Time'
        yAxisLabel='Current [A]'
        hoverTemplate='<b>Time:</b> %{customdata[0]}<br><b>Current:</b> %{customdata[1]} A<extra></extra>'
      />

      <Card sx={{ flexGrow: 1, my: 2, py: 0, px: 2 }}>
        <Table sx={{ minWidth: 300 }}>
          <TableBody>
            <TableRow>
              <TableCell sx={{ border: 0, pl: 0, pr: 2, width: '30%' }}>
                <Typography>Number of Datapoints loaded:</Typography>
              </TableCell>
              <TableCell sx={{ border: 0, pl: 0 }}>
                <Typography>{data?.current.length}</Typography>
              </TableCell>
              <TableCell colSpan={2} sx={{ border: 0, pl: 0 }}>
                <DownloadCSVButton
                  data={{
                    timestamp: data?.timestamp ?? [],
                    current: data?.current ?? [],
                  }}
                  defaultFilename={`em${deviceId}_${startDate?.toLocaleDateString()}T${startDate?.toLocaleTimeString()}`}
                />
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell sx={{ border: 0, pl: 0, pr: 2 }}>
                <Typography>Integrated Charge:</Typography>
              </TableCell>
              <TableCell sx={{ border: 0, pl: 0 }}>
                <Typography>
                  {integratedCharge ? integratedCharge.toExponential(6) : 'N/A'}{' '}
                  C
                </Typography>
              </TableCell>
              <TableCell sx={{ border: 0, pl: 0, pr: 2 }}>
                <TextField
                  variant='outlined'
                  size='small'
                  label={'Conversion Factor [Gy/C]'}
                  value={conversionFactor}
                  onChange={(e) => {
                    const value = parseFloat(e.target.value)
                    if (!isNaN(value)) {
                      setConversionFactor(value)
                    }
                  }}
                  type={'number'}
                />
              </TableCell>
              <TableCell sx={{ border: 0, pl: 0 }}>
                <Typography>
                  {integratedCharge
                    ? (integratedCharge * conversionFactor).toExponential(6)
                    : 'N/A'}{' '}
                  Gy
                </Typography>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </Card>


      <Box
        sx={{
          flexGrow: 1,
          mb: 1,
          p: 2,
          display: 'flex',
          gap: 2,
          flexWrap: 'wrap',
          justifyContent: 'center',
        }}
      >
        <ExecQueryButton
          startIcon={<PlayArrowIcon />}
          onClick={async () => {
            return await ElectrometerService.electrometerStartContinuousMeasurement(
              deviceIdPathArg,
            )
          }}
        >
          Start Continuous
        </ExecQueryButton>
        <ExecQueryButton
          startIcon={<StopIcon />}
          onClick={async () => {
            return await ElectrometerService.electrometerStopContinuousMeasurement(
              deviceIdPathArg,
            )
          }}
        >
          Stop Continuous
        </ExecQueryButton>
        <ExecQueryButton
          startIcon={<HourglassBottomIcon />}
          onClick={async () => {
            return await ElectrometerService.electrometerStartTriggerBasedMeasurement(
              deviceIdPathArg,
            )
          }}
        >
          Start Trigger
        </ExecQueryButton>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            flexGrow: 1,
          }}
        >
          <Typography variant='h6'>Current Range Settings</Typography>
          <DirtyTextField
            label={'Auto Current Range [ON/OFF]'}
            onOff={true}
            value={settings?.current_range_auto ?? ''}
            onApply={makeSettingApplyHandler('current_range_auto')}
            disabled={state?.status !== 'idle'}
          />
          <DirtyTextField
            label={'Manual Current Range [A]'}
            value={settings?.current_range ?? ''}
            onApply={makeSettingApplyHandler('current_range')}
            disabled={settings?.current_range_auto == 'ON' || state?.status !== 'idle'}
          />
          <DirtyTextField
            label={'Auto Current Range Upper Limit [A]'}
            value={settings?.current_range_auto_upper_limit ?? ''}
            onApply={makeSettingApplyHandler('current_range_auto_upper_limit')}
            disabled={settings?.current_range_auto == 'OFF' || state?.status !== 'idle'}
          />
          <DirtyTextField
            label={'Auto Current Range Lower Limit [A]'}
            value={settings?.current_range_auto_lower_limit ?? ''}
            onApply={makeSettingApplyHandler('current_range_auto_lower_limit')}
            disabled={settings?.current_range_auto == 'OFF' || state?.status !== 'idle'}
          />
        </Box>

        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            flexGrow: 1,
          }}
        >
          <Typography variant='h6'>Aperture Settings</Typography>
          <DirtyTextField
            label={'Auto Aperture [ON/OFF]'}
            onOff={true}
            value={settings?.aperture_auto ?? ''}
            onApply={makeSettingApplyHandler('aperture_auto')}
            disabled={state?.status !== 'idle'}
          />
          <DirtyTextField
            label={'Manual Aperture Integration Time [s]'}
            value={settings?.aperture_integration_time ?? ''}
            onApply={makeSettingApplyHandler('aperture_integration_time')}
            disabled={settings?.aperture_auto == 'ON' || state?.status !== 'idle'}
          />
        </Box>

        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            flexGrow: 1,
          }}
        >
          <Typography variant='h6'>Trigger Settings</Typography>
          <DirtyTextField
            label={'Trigger Count [#]'}
            value={settings?.trigger_count ?? ''}
            onApply={makeSettingApplyHandler('trigger_count')}
            onChange={(e) => setTriggerCount(Number(e.target.value) || 0)}
            disabled={state?.status !== 'idle'}
          />
          <DirtyTextField
            label={'Trigger Time Interval [s]'}
            value={settings?.trigger_time_interval ?? ''}
            onApply={makeSettingApplyHandler('trigger_time_interval')}
            onChange={(e) => setTriggerTime(Number(e.target.value) || 0)}
            disabled={state?.status !== 'idle'}
          />
          <Typography>
            Total Measurement Time: {triggerCount * triggerTime} s
          </Typography>
          <DirtyTextField
            label={'Trigger Delay [s]'}
            value={settings?.trigger_delay ?? ''}
            onApply={makeSettingApplyHandler('trigger_delay')}
            disabled={state?.status !== 'idle'}
          />
        </Box>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            flexGrow: 1,
          }}
        >
          <Typography variant='h6'>Bias Voltage Control</Typography>
          <DirtyTextField
            label={'Start [V]'}
            value={settings?.voltage_start ?? ''}
            onApply={makeSettingApplyHandler('voltage_start')}
          />
          <DirtyTextField
            label={'Stop [V]'}
            value={settings?.voltage_stop ?? ''}
            onApply={makeSettingApplyHandler('voltage_stop')}
          />
          <DirtyTextField
            label={'Step [V]'}
            value={settings?.voltage_step ?? ''}
            onApply={makeSettingApplyHandler('voltage_step')}
          />
          <DirtyTextField
            label={'Settle Time [s]'}
            value={settings?.voltage_settle_time ?? ''}
            onApply={makeSettingApplyHandler('voltage_settle_time')}
          />
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            <ExecQueryButton
              startIcon={<FlashOnIcon />}
              onClick={async () => {
                return await ElectrometerService.electrometerStartSourceVoltageSweep(
                  deviceIdPathArg,
                )
              }}
            >
              Start Voltage Sweep
            </ExecQueryButton>
            <ExecQueryButton
              startIcon={<FlashOffIcon />}
              onClick={async () => {
                return await ElectrometerService.electrometerTurnOffSourceVoltage(
                  deviceIdPathArg,
                )
              }}
            >
              Turn Off Voltage
            </ExecQueryButton>
          </Box>
        </Box>
      </Box>
    </Box>
  )
}

export default Electrometer
