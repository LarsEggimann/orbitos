import React, { useState, useEffect } from 'react'
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
import AutorenewIcon from '@mui/icons-material/Autorenew';
import BoltIcon from '@mui/icons-material/Bolt';
import HomeIcon from '@mui/icons-material/Home';
import ControlCameraIcon from '@mui/icons-material/ControlCamera';
import TimeSeriesChart from '~/components/plots/TimeSeriesPlot'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import ConnectionButtons from '~/components/ui/ConnectionButtons'
import {
  Chopperwheel as ChopperwheelService,
  type CwDataResponse,
  type CwState,
  type CwSettings,
} from '~/generated'
import { useDeviceWebSocket } from '~/utils/webSocketHook'
import { CwStateDisplay } from '~/components/chopperwheel/CwStateDisplay'
import DateRangeSelect from '~/components/ui/DataRangeSelection'
import DirtyTextField from '~/components/ui/DirtyTextField'
import DownloadCSVButton from '~/components/ui/DownloadCSVButton'
import { useSnackbarContext } from '~/provider/SnackbarProvider'
import { useConfig } from '~/provider/ConfigProvider'
import { MenuItem, TextField } from '@mui/material'
import CwPosVeloPlot from './CwPosVeloPlot'

const Chopperwheel: React.FC = () => {
  const { API_WEBSOCKET_URL } = useConfig()
  const deviceName = 'chopperwheel'

  const [startDate, setStartDate] = React.useState(null as Date | null)
  const [endDate, setEndDate] = React.useState(null as Date | null)
  const [datesLoaded, setDatesLoaded] = useState(false)
  const [moveToPosition, setMoveToPosition] = useState<number | null>(null)

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

  // persist moveToPosition in localStorage
  useEffect(() => {
    const savedPosition = localStorage.getItem(`${deviceName}_moveToPosition`)
    if (savedPosition) {
      setMoveToPosition(Number(savedPosition))
    }
  }, [deviceName])

  useEffect(() => {
    try {
      if (moveToPosition !== null) {
        localStorage.setItem(
          `${deviceName}_moveToPosition`,
          moveToPosition.toString(),
        )
      }
    } catch (error) {
      console.error('Error saving moveToPosition to localStorage:', error)
    }
  }, [moveToPosition, deviceName])

  const [data, setData] = useState<CwDataResponse | undefined>(undefined)

  const dataQuery = useQuery({
    queryKey: [deviceName, startDate, endDate],
    queryFn: async () => {
      const response =
        await ChopperwheelService.chopperwheelGetChopperWheelData({
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
    CwState,
    CwDataResponse,
    CwSettings
  >({
    url: `${API_WEBSOCKET_URL}/chopperwheel/ws`,
    fetchInitialState: async () =>
      (await ChopperwheelService.chopperwheelGetChopperWheelState()).data!,
    fetchInitialSettings: async () =>
      (await ChopperwheelService.chopperwheelGetChopperWheelSettings()).data!,
    dataAppendFunction: (newData) => {
      setData((prevData) => {
        if (!prevData) return newData
        return {
          device_name: prevData.device_name,
          timestamp: prevData.timestamp.concat(newData.timestamp),
          velocity: prevData.velocity.concat(newData.velocity),
          angular_position: prevData.angular_position.concat(
            newData.angular_position,
          ),
        }
      })
    },
  })

  const { openSnackbar } = useSnackbarContext()

  const setSettingsQuery = useMutation({
    mutationFn: async (settings: Record<string, any>) => {
      return await ChopperwheelService.chopperwheelSetChopperWheelSettings({
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

  const [comPort, setComPort] = useState<string>('') // Default COM port, can be changed later

  const { data: comPortsData, isLoading: comPortsLoading } = useQuery({
    queryKey: ['chopperwheel-com-ports'],
    queryFn: async () => {
      const response =
        await ChopperwheelService.chopperwheelGetAvailableComPorts()
      return response.data
    },
    refetchOnWindowFocus: true,
  })

  return (
    <Box sx={{ bgcolor: 'background.paper' }}>
      <Stack
        direction='row'
        sx={{ alignItems: 'center', justifyContent: 'space-between' }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant='h5' sx={{ mb: 0 }}>
            Chopperwheel -
          </Typography>
          <Typography
            variant='subtitle1'
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            {state?.connection_status == 'connected' ? '🟢' : '🔴'}
          </Typography>
        </Box>
        <Typography variant='subtitle1'>
          Live State via WebSocket {connected ? '🟢' : '🔴'}
        </Typography>
      </Stack>
      <Divider sx={{ my: 2, mt: 0 }} />

      <Stack direction='row' sx={{ alignItems: 'center', gap: 2, my: 2 }}>
        <TextField
          size='small'
          variant='outlined'
          label='Select Serial Port'
          select
          value={comPort}
          onChange={(e) => setComPort(e.target.value as string)}
          sx={{ minWidth: 250 }}
          disabled={comPortsLoading}
        >
          {comPortsData?.length === 0 && (
            <MenuItem value='' disabled>
              No COM ports found
            </MenuItem>
          )}
          {comPortsData &&
            comPortsData.map((port) => (
              <MenuItem key={port.port} value={port.port}>
                {port.port} - {port.description}
              </MenuItem>
            ))}
        </TextField>
        <ConnectionButtons
          connectionStatus={state?.connection_status}
          onConnect={async () => {
            if (!comPort) {
              throw new Error(
                'You need to select a COM port before connecting!',
              )
            }
            return await ChopperwheelService.chopperwheelConnectToChopperWheel({
              path: { com_port: comPort },
            })
          }}
          onDisconnect={async () => {
            return await ChopperwheelService.chopperwheelDisconnectChopperWheel()
          }}
          additionalConnectValidation={!!comPort}
          showResetError={true}
          onResetError={async () => {
            return await ChopperwheelService.chopperwheelResetChopperWheelError()
          }}
        />
      </Stack>

      <DateRangeSelect
        startState={[startDate, setStartDate]}
        endState={[endDate, setEndDate]}
      ></DateRangeSelect>

      <Card sx={{ flexGrow: 1, my: 1, p: 2 }}>
        <Typography variant='h6'>Plot Data</Typography>
        <Table sx={{ minWidth: 400, tableLayout: 'fixed' }}>
          <TableBody>
            <TableRow>
              <TableCell sx={{ border: 0, pl: 0, pr: 2, width: '35%' }}>
                <Typography>Number of Datapoints loaded:</Typography>
              </TableCell>
              <TableCell sx={{ border: 0, pl: 0, width: '15%' }}>
                <Typography>{data?.velocity.length}</Typography>
              </TableCell>
              <TableCell colSpan={2} sx={{ border: 0, pl: 0, width: '50%' }}>
                <DownloadCSVButton
                  data={{
                    timestamp: data?.timestamp ?? [],
                    velocity: data?.velocity ?? [],
                    angular_position: data?.angular_position ?? [],
                  }}
                  defaultFilename={`chopperwheel_${startDate?.toLocaleDateString()}T${startDate?.toLocaleTimeString()}`}
                />
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell sx={{ border: 0, pl: 0, pr: 2, width: '35%' }}>
                <Typography>Latest Velocity:</Typography>
              </TableCell>
              <TableCell sx={{ border: 0, pl: 0, width: '15%' }}>
                <Typography>
                  {typeof data?.velocity?.[data?.velocity.length - 1] ===
                    'number'
                    ? data?.velocity[data?.velocity.length - 1].toFixed(3) +
                    ' rps'
                    : ''}
                </Typography>
              </TableCell>
              <TableCell sx={{ border: 0, pl: 0, pr: 2, width: '25%' }}>
                <Typography>Latest Angular Position:</Typography>
              </TableCell>
              <TableCell sx={{ border: 0, pl: 0, width: '25%' }}>
                <Typography>
                  {typeof data?.angular_position?.[
                    data?.angular_position.length - 1
                  ] === 'number'
                    ? data?.angular_position[
                      data?.angular_position.length - 1
                    ].toFixed(3) + ' °'
                    : ''}
                </Typography>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </Card>

      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          gap: 1,
          width: '100%',
        }}
      >
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <CwPosVeloPlot
            xData={data?.angular_position ?? []}
            yData={data?.velocity ?? []}
            dataQuery={dataQuery}
            height={500}
            xAxisLabel='Angular Position [deg]'
            yAxisLabel='Velocity [rps]'
            hoverTemplate='<b>Angular Position:</b> %{customdata[0]}<br><b>Velocity:</b> %{customdata[1]} deg<extra></extra>'
          />
        </Box>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <TimeSeriesChart
            xData={data?.timestamp ?? []}
            yData={data?.velocity ?? []}
            dataQuery={dataQuery}
            height={500}
            xAxisLabel='Time'
            yAxisLabel='Velocity [rps]'
            hoverTemplate='<b>Time:</b> %{customdata[0]}<br><b>Velocity:</b> %{customdata[1]} rps<extra></extra>'
          />
        </Box>
      </Box>

      <CwStateDisplay state={state as CwState} />

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
          startIcon={<AutorenewIcon />}
          onClick={async () => {
            return await ChopperwheelService.chopperwheelRotateDemoChopperWheel()
          }}
        >
          Rotate Demo
        </ExecQueryButton>
        <ExecQueryButton
          startIcon={<BoltIcon />}
          onClick={async () => {
            return await ChopperwheelService.chopperwheelFlashBeamChopperWheel()
          }}
        >
          Flash Beam
        </ExecQueryButton>
        <ExecQueryButton
          startIcon={<HomeIcon />}
          onClick={async () => {
            return await ChopperwheelService.chopperwheelFindHomeChopperWheel()
          }}
        >
          Find Home
        </ExecQueryButton>
        <Box
          sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
        >
          <ExecQueryButton
            startIcon={<ControlCameraIcon />}
            onClick={async () => {
              return await ChopperwheelService.chopperwheelGoToPositionChopperWheel({
                path: { angle_deg: moveToPosition! },
              })
            }}
          >
            Move To Position
          </ExecQueryButton>
          <TextField
            variant='outlined'
            size='small'
            label='Move to Position [deg]'
            value={moveToPosition}
            onChange={(e) => {
              setMoveToPosition(Number(e.target.value))
            }}
            type={'number'}
          />
          <Typography>
            Open Position: XXX° for New Wheel (v2) with new mount.
            <br />
            TODO: Add correct angle!!
          </Typography>

        </Box>
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
          <Typography variant='h6'>Motor Settings</Typography>
          <DirtyTextField
            label={'Max Velocity [rps]'}
            value={settings?.max_velocity ?? ''}
            onApply={makeSettingApplyHandler('max_velocity')}
          />
          <DirtyTextField
            label={'Max Acceleration [rps²]'}
            value={settings?.max_acceleration ?? ''}
            onApply={makeSettingApplyHandler('max_acceleration')}
          />
          <DirtyTextField
            label={'Max Current [0-255]'}
            value={settings?.max_current ?? ''}
            onApply={makeSettingApplyHandler('max_current')}
          />
          <DirtyTextField
            label={'Boost Current [0-255]'}
            value={settings?.boost_current ?? ''}
            onApply={makeSettingApplyHandler('boost_current')}
          />
          <DirtyTextField
            label={'Standby Current [0-255]'}
            value={settings?.standby_current ?? ''}
            onApply={makeSettingApplyHandler('standby_current')}
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
          <Typography variant='h6'>General Settings</Typography>
          <DirtyTextField
            label={'Time delay after flash beam request [s]'}
            value={settings?.flash_beam_delay ?? ''}
            onApply={makeSettingApplyHandler('flash_beam_delay')}
          />
          <DirtyTextField
            label={
              'Angle (in home position) between slit and start of beam pipe [°]'
            }
            value={settings?.angle_home_sens_to_beam_pipe ?? ''}
            onApply={makeSettingApplyHandler('angle_home_sens_to_beam_pipe')}
          />
          <Typography>
            This angle is used to execute the flash rotation pattern. The wheel
            will rotate 360° + the angle set above, after this it will rotate
            back by the angle amount set above. This should place the wheel in
            home position again.
            <br />
            Suggested Angles:
            <ul>
              <li>275° - New Wheel (v2) with new mount</li>
              <li>140° - Small Wheel (v1) with new mount</li>
              <li>290° - Small Wheel (v1) with old mount</li>
            </ul>
          </Typography>
        </Box>
      </Box>
    </Box>
  )
}

export default Chopperwheel
