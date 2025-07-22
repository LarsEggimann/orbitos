import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Divider from '@mui/material/Divider'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'
import FormControlLabel from '@mui/material/FormControlLabel'
import {
  Chopperwheel as ChopperwheelService,
  type CwDataResponse,
  Electrometer as ElectrometerService,
  type ElectrometerDataResponse,
} from '~/generated'
import DateRangeSelect from '~/components/ui/DataRangeSelection'
import DeviceMultiSelect, { type DeviceType } from '../ui/DeviceMultiSelect'
import MultiTimeSeriesPlot from '../plots/MultiTimeSeriesPlot'
import ScatterPlot from '../plots/ScatterPlot'

const ComboDataView: React.FC = () => {
  const pageName = 'combo-data-view'

  const [startDate, setStartDate] = React.useState(null as Date | null)
  const [endDate, setEndDate] = React.useState(null as Date | null)
  const [datesLoaded, setDatesLoaded] = useState(false)

  // persist date range in localStorage using deviceIdFull as key
  useEffect(() => {
    const savedStart = localStorage.getItem(`${pageName}_startDate`)
    const savedEnd = localStorage.getItem(`${pageName}_endDate`)
    if (savedStart) {
      setStartDate(new Date(savedStart))
    } else {
      // Default to 12 hours ago if no start date is saved
      setStartDate(new Date(Date.now() - 12 * 60 * 60 * 1000)) // 12 hours ago
    }
    if (savedEnd) setEndDate(new Date(savedEnd))
    setDatesLoaded(true)
  }, [pageName])

  useEffect(() => {
    try {
      if (startDate)
        localStorage.setItem(`${pageName}_startDate`, startDate.toISOString())
      if (endDate) {
        localStorage.setItem(`${pageName}_endDate`, endDate.toISOString())
      } else {
        // if endDate is null, clear it from localStorage, this allows to reset the end date
        localStorage.removeItem(`${pageName}_endDate`)
      }
    } catch (error) {
      console.error('Error saving date range to localStorage:', error)
    }
  }, [startDate, endDate, pageName])

  const [selectedDevices, setSelectedDevices] = useState<DeviceType[]>(() => {
    const saved = localStorage.getItem('combo_data_view_selected_devices')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed)) return parsed
      } catch { }
    }
    return []
  })

  // Auto-reload functionality
  const [autoReload, setAutoReload] = useState<boolean>(() => {
    const saved = localStorage.getItem('combo_data_view_auto_reload')
    return saved ? JSON.parse(saved) : false
  })

  const autoReloadIntervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    localStorage.setItem(
      'combo_data_view_selected_devices',
      JSON.stringify(selectedDevices),
    )
  }, [selectedDevices])

  useEffect(() => {
    localStorage.setItem(
      'combo_data_view_auto_reload',
      JSON.stringify(autoReload),
    )
  }, [autoReload])

  const getQueryArgs = () => ({
    query: {
      start: startDate?.toISOString(),
      end: endDate?.toISOString(),
    },
  })

  const [cwData, setCwData] = useState<CwDataResponse | undefined>(undefined)
  const cwQuery = useQuery({
    queryKey: ['cwData', startDate, endDate],
    queryFn: async () => {
      const response =
        await ChopperwheelService.chopperwheelGetChopperWheelData(
          getQueryArgs(),
        )
      setCwData(response.data)
      return response.data
    },
    refetchOnWindowFocus: true,
    enabled: datesLoaded && selectedDevices.includes('chopperwheel'),
  })

  const [em1Data, setEm1Data] = useState<ElectrometerDataResponse | undefined>(
    undefined,
  )
  const em1Query = useQuery({
    queryKey: ['em1Data', startDate, endDate],
    queryFn: async () => {
      const response = await ElectrometerService.electrometerGetCurrentData({
        path: { device_id: 1 },
        ...getQueryArgs(),
      })
      setEm1Data(response.data)
      return response.data
    },
    refetchOnWindowFocus: true,
    enabled: datesLoaded && selectedDevices.includes('electrometer_1'),
  })

  const [em2Data, setEm2Data] = useState<ElectrometerDataResponse | undefined>(
    undefined,
  )
  const em2Query = useQuery({
    queryKey: ['em2Data', startDate, endDate],
    queryFn: async () => {
      const response = await ElectrometerService.electrometerGetCurrentData({
        path: { device_id: 2 },
        ...getQueryArgs(),
      })
      setEm2Data(response.data)
      return response.data
    },
    refetchOnWindowFocus: true,
    enabled: datesLoaded && selectedDevices.includes('electrometer_2'),
  })

  // Auto-reload functionality - simple interval-based refetching
  const refetchQueries = useCallback(() => {
    if (selectedDevices.includes('chopperwheel') && cwQuery.refetch) {
      cwQuery.refetch()
    }
    if (selectedDevices.includes('electrometer_1') && em1Query.refetch) {
      em1Query.refetch()
    }
    if (selectedDevices.includes('electrometer_2') && em2Query.refetch) {
      em2Query.refetch()
    }
  }, [selectedDevices, cwQuery.refetch, em1Query.refetch, em2Query.refetch])

  useEffect(() => {
    if (autoReload) {
      autoReloadIntervalRef.current = setInterval(() => {
        refetchQueries()
      }, 60000) // 1 minute = 60000ms
    } else if (autoReloadIntervalRef.current) {
      clearInterval(autoReloadIntervalRef.current)
      autoReloadIntervalRef.current = null
    }

    // Cleanup on unmount
    return () => {
      if (autoReloadIntervalRef.current) {
        clearInterval(autoReloadIntervalRef.current)
      }
    }
  }, [autoReload, refetchQueries])

  // Build the series array based on selected devices and update when selectedDevices, cwData, em1Data, em2Data, startDate, or endDate changes
  const [series, setSeries] = useState<any[]>([])
  useEffect(() => {
    const newSeries = []
    if (selectedDevices.includes('chopperwheel')) {
      newSeries.push(
        {
          label: 'CW Angular Position',
          x: cwData?.timestamp || [],
          y: cwData?.angular_position || [],
          yLabel: 'Angular Position [°]',
        },
        {
          label: 'CW Velocity',
          x: cwData?.timestamp || [],
          y: cwData?.velocity || [],
          yLabel: 'Velocity [rps]',
        },
      )
    }
    if (selectedDevices.includes('electrometer_1')) {
      newSeries.push({
        label: 'EM1 Current',
        x: em1Data?.timestamp || [],
        y: em1Data?.current || [],
        yLabel: 'Current [A]',
        lineColor: '#ff0000',
      })
    }
    if (selectedDevices.includes('electrometer_2')) {
      newSeries.push({
        label: 'EM2 Current',
        x: em2Data?.timestamp || [],
        y: em2Data?.current || [],
        yLabel: 'Current [A]',
        lineColor: '#00ff00',
      })
    }
    setSeries(newSeries)
  }, [selectedDevices, cwData, em1Data, em2Data, startDate, endDate])

  const [selectedOnlyElectrometers, setSelectedOnlyElectrometers] = useState<boolean>(false)
  useEffect(() => {
    if (selectedDevices.includes('electrometer_1') && selectedDevices.includes('electrometer_2') && !selectedDevices.includes('chopperwheel')) {
      setSelectedOnlyElectrometers(true)
    } else {
      setSelectedOnlyElectrometers(false)
    }
  }, [selectedDevices])

  return (
    <Box sx={{ bgcolor: 'background.paper' }}>
      <Stack
        direction='row'
        sx={{ alignItems: 'center', justifyContent: 'space-between' }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant='h5' sx={{ mb: 0 }}>
            Combo Data View
          </Typography>
          <DeviceMultiSelect
            selectedDevices={selectedDevices}
            setSelectedDevices={setSelectedDevices}
            label='Select Devices for Actions'
            minWidth={300}
          />
        </Box>
        <FormControlLabel
          control={
            <Switch
              checked={autoReload}
              onChange={(e) => setAutoReload(e.target.checked)}
              color="primary"
            />
          }
          label="Auto-reload (1 min)"
          sx={{ mb: 0 }}
        />
      </Stack>
      <Divider sx={{ mb: 5, mt: 2 }} />

      <DateRangeSelect
        startState={[startDate, setStartDate]}
        endState={[endDate, setEndDate]}
      ></DateRangeSelect>

      <MultiTimeSeriesPlot
        series={series}
        dataQueries={[cwQuery, em1Query, em2Query]}
      />

      {selectedOnlyElectrometers && (
        <Box sx={{ mt: 2 }}>
          <ScatterPlot
            xData={em1Data?.current || []}
            yData={em2Data?.current || []}
            title='EM 1 vs EM 2 Correlation'
            xAxisLabel='EM 1 Current [A]'
            yAxisLabel='EM 2 Current [A]'
          />
        </Box>
      )}
    </Box>
  )
}

export default ComboDataView
