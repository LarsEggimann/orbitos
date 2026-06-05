import React, { useEffect, useMemo, useState } from 'react'
import type { UseQueryResult } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import { useTheme } from '@mui/material/styles'
import { fromTimestampToLocalizedString } from '~/utils/helpers'
import Plot from '~/components/plots/Plot'

export interface TimeSeriesData {
  label: string
  x: (string | number | null)[]
  y: (number | null)[]
  yLabel?: string
  lineColor?: string
}

interface MultiTimeSeriesPlotProps {
  series: TimeSeriesData[]
  dataQueries?: UseQueryResult<any, Error>[]
  title?: string
  xAxisLabel?: string
  height?: string | number
}

type PlotlyFigure = {
  data: Plotly.Data[]
  layout: Partial<Plotly.Layout>
  frames?: Plotly.Frame[] | null
  config?: Partial<Plotly.Config>
}

const MultiTimeSeriesPlot: React.FC<MultiTimeSeriesPlotProps> = ({
  series,
  dataQueries,
  title,
  xAxisLabel = 'Time',
  height = '600px',
}) => {
  const muiTheme = useTheme()

  const textColor = muiTheme.palette.text.primary
  const gridColor = muiTheme.palette.divider
  const tooltipBgColor = muiTheme.palette.background.paper
  const tooltipBorderColor = muiTheme.palette.divider
  const bgColor = 'transparent'

  // Convert x values if they are timestamps (numbers)
  const [localizedSeries, setLocalizedSeries] = useState<TimeSeriesData[]>([])

  useEffect(() => {
    setLocalizedSeries(
      series.map((s) => {
        // If all x values are numbers, treat as timestamps
        if (s.x.length > 0 && typeof s.x[0] === 'number') {
          const localizedX = (s.x as number[]).map((val) =>
            fromTimestampToLocalizedString(val),
          )
          return { ...s, x: localizedX }
        }
        return s
      }),
    )
  }, [series])

  const getPlotData = (): Plotly.Data[] => {
    return localizedSeries.map((s, idx) => {
      let yaxisName = 'y'
      if (s.yLabel) {
        yaxisName = idx === 0 ? 'y' : `y${idx + 1}`
      }
      return {
        x: s.x,
        y: s.y,
        name: s.label,
        type: 'scatter',
        mode: 'lines',
        yaxis: yaxisName,
        hoverlabel: {
          bgcolor: tooltipBgColor,
          bordercolor: tooltipBorderColor,
          font: {
            family: 'Inter, sans-serif',
            size: 12,
            color: textColor,
          },
        },
      }
    })
  }

  const getLayout = (): Partial<Plotly.Layout> => {
    // Build y-axes if needed
    const yAxes: Record<string, any> = {}
    localizedSeries.forEach((s, idx) => {
      const axisKey = `yaxis${idx === 0 ? '' : idx + 1}`
      yAxes[axisKey] = {
        title: {
          text: s.yLabel || 'Value',
          standoff: 5,
        },
        automargin: true,
        showgrid: false,
        showline: false,
        gridwidth: 0.4,
        gridcolor: gridColor,
        overlaying: idx === 0 ? undefined : 'y',
        side: idx % 2 === 0 ? 'left' : 'right',
        position: idx === 0 ? undefined : 1 - (idx - 1) * 0.05,
      }
    })
    return {
      title: {
        text: title,
        font: { color: textColor },
      },
      font: {
        color: textColor,
        size: 16,
      },
      autosize: true,
      paper_bgcolor: bgColor,
      plot_bgcolor: bgColor,
      xaxis: {
        title: {
          text: xAxisLabel,
          standoff: 5,
        },
        automargin: true,
        showgrid: false,
        showline: false,
        gridwidth: 0.4,
        gridcolor: gridColor,
      },
      margin: { l: 20, r: 20, t: 20, b: 20 },
      ...yAxes,
    }
  }

  const getConfig = (): Partial<Plotly.Config> => {
    return {
      responsive: true,
      displaylogo: false,
      displayModeBar: 'hover',
      modeBarButtonsToRemove: [
        'toImage',
        'zoomIn2d',
        'zoomOut2d',
        'autoScale2d',
      ],
    }
  }

  const getFigure = (): PlotlyFigure => {
    return {
      data: getPlotData(),
      layout: getLayout(),
      config: getConfig(),
    }
  }

  const [figure, setFigure] = useState<PlotlyFigure>(getFigure())

  useMemo(() => {
    setFigure((prevFigure) => ({
      ...prevFigure,
      data: getPlotData(),
    }))
  }, [localizedSeries, textColor])

  useEffect(() => {
    setFigure(getFigure())
  }, [dataQueries, muiTheme, localizedSeries])

  // Compute a combined loading state if multiple queries are provided
  const isLoading = Array.isArray(dataQueries)
    ? dataQueries.some((q) => q?.isLoading || q?.isFetching)
    : false

  return (
    <Box sx={{ position: 'relative', width: '100%', height: height }}>
      <Box
        sx={{
          opacity: isLoading ? 0.3 : 1,
          transition: 'opacity 0.2s',
          width: '100%',
          height: height,
        }}
      >
        <Plot
          data={figure.data}
          layout={figure.layout}
          frames={figure.frames || []}
          config={figure.config}
          useResizeHandler={true}
          style={{ width: '100%', height: height }}
        />
      </Box>
    </Box>
  )
}

export default MultiTimeSeriesPlot
