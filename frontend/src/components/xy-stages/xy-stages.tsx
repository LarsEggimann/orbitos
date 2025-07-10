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

import TimeSeriesChart from '~/components/plots/TimeSeriesPlot'
import ExecQueryButton from '~/components/ui/ExecQueryButton'
import {
  XyStages as XyStagesService,
  type XyStagesDataResponse,
  type XyStagesState,
  type XyStagesSettings,
} from '~/generated'
import { useDeviceWebSocket } from '~/utils/webSocketHook'
import DateRangeSelect from '~/components/ui/DataRangeSelection'
import DirtyTextField from '~/components/ui/DirtyTextField'
import DownloadCSVButton from '~/components/ui/DownloadCSVButton'
import { useSnackbarContext } from '~/provider/SnackbarProvider'
import { useConfig } from '~/provider/ConfigProvider'
import { MenuItem, TextField } from '@mui/material'
import MultiTimeSeriesPlot from '../plots/MultiTimeSeriesPlot'
import { XyStagesStateDisplay } from './XYStagesStateDisplay'

const XyStages: React.FC = () => {
  const { API_WEBSOCKET_URL } = useConfig()
  const deviceName = 'xy-stages'

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

  const [data, setData] = useState<XyStagesDataResponse | undefined>(undefined)

  const dataQuery = useQuery({
    queryKey: [deviceName, startDate, endDate],
    queryFn: async () => {
      const response =
        await XyStagesService.xyStagesGetStagesData({
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
    XyStagesState,
    XyStagesDataResponse,
    XyStagesSettings
  >({
    url: `${API_WEBSOCKET_URL}/xy-stages/ws`,
    fetchInitialState: async () =>
      (await XyStagesService.xyStagesGetStagesState()).data!,
    fetchInitialSettings: async () =>
      (await XyStagesService.xyStagesGetStagesSettings()).data!,
    dataAppendFunction: (newData) => {
      setData((prevData) => {
        if (!prevData) return newData
        return {
          device_name: prevData.device_name,
          timestamp: prevData.timestamp.concat(newData.timestamp),
          x_position: prevData.x_position.concat(newData.x_position),
          y_position: prevData.y_position.concat(
            newData.y_position,
          ),
        }
      })
    },
  })

  const { openSnackbar } = useSnackbarContext()

  const setSettingsQuery = useMutation({
    mutationFn: async (settings: Record<string, any>) => {
      return await XyStagesService.xyStagesSetStagesSettings({
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


  const [xIndex, setXIndex] = useState<number>(1) // Default X index
  const [yIndex, setYIndex] = useState<number>(0) // Default Y index

  const { data: comPortsData, isLoading: comPortsLoading } = useQuery({
    queryKey: ['xy-stages-com-ports'],
    queryFn: async () => {
      const response =
        await XyStagesService.xyStagesGetAvailableUsbDevices()
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
            XY - Stages -
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
          label='Select x-axis USB Device'
          select
          value={xIndex}
          onChange={(e) => setXIndex(Number(e.target.value))}
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
              <MenuItem key={port.index} value={port.index}>
                {port.index} - {port.description}
              </MenuItem>
            ))}
        </TextField>
        <ExecQueryButton
          onClick={async () => {
            if (!xIndex) {
              throw new Error(
                'You need to select a COM port before connecting!',
              )
            }
            return await XyStagesService.xyStagesConnectToStage({
              path: { axis: 'x-axis', index: xIndex },
            })
          }}
          disabled={!xIndex || state?.x_state?.connection_status == 'connected'}
        >
          Connect
        </ExecQueryButton>
        <ExecQueryButton
          onClick={async () => {
            return await XyStagesService.xyStagesDisconnectStage({
              path: { axis: 'x-axis' },
            })
          }}
          disabled={state?.x_state?.connection_status == 'disconnected'}
          color='warning'
        >
          Disconnect
        </ExecQueryButton>
        <Box flexGrow={1}></Box>
        <ExecQueryButton
          onClick={async () => {
            return await XyStagesService.xyStagesResetStagesError()
          }}
        >
          Reset Error
        </ExecQueryButton>
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
                <Typography>{data?.x_position.length}</Typography>
              </TableCell>
              <TableCell colSpan={2} sx={{ border: 0, pl: 0, width: '50%' }}>
                <DownloadCSVButton
                  data={{
                    timestamp: data?.timestamp ?? [],
                    x_position: data?.x_position ?? [],
                    y_position: data?.y_position ?? [],
                  }}
                  defaultFilename={`xy_stages_${startDate?.toLocaleDateString()}T${startDate?.toLocaleTimeString()}`}
                />
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
          {/* <TimeSeriesChart
            xData={data?.timestamp ?? []}
            yData={data?.x_position ?? []}
            dataQuery={dataQuery}
            height={500}
            xAxisLabel='Placeholder [deg]'
            yAxisLabel='Placeholder [rps]'
          /> */}
        </Box>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <MultiTimeSeriesPlot
            series={
              [
                {
                  label: 'X Position',
                  x: data?.timestamp ?? [],
                  y: data?.x_position ?? [],
                  yLabel: 'X Position [mm]',
                },
                {
                  label: 'Y Position',
                  x: data?.timestamp ?? [],
                  y: data?.y_position ?? [],
                  yLabel: 'Y Position [mm]',
                },
              ]
            }
            dataQueries={[dataQuery]}
          />
        </Box>
      </Box>

      <XyStagesStateDisplay state={state as XyStagesState} />


      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            flexGrow: 1,
          }}
        >
          <Typography variant='h6'>Direction Settings</Typography>
          <DirtyTextField
            label={'X direction modifier [-1 or 1]'}
            value={settings?.x_direction_modifier ?? ''}
            onApply={makeSettingApplyHandler('x_direction_modifier')}
          />
          <DirtyTextField
            label={'Y direction modifier [-1 or 1]'}
            value={settings?.y_direction_modifier ?? ''}
            onApply={makeSettingApplyHandler('y_direction_modifier')}
          />
          <Typography>
            The direction modifier is used to invert the direction of the axis position reading. This also inverts the movement control, everything is relative to the 0 and then scaled by this modifier. 
          </Typography>
        </Box>

      </Box>
    </Box>
  )
}

export default XyStages
