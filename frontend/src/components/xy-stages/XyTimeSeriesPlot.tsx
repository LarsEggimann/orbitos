import React, { useEffect, useMemo, useState } from 'react'
import Plot from 'react-plotly.js'
import { fromTimestampToLocalizedString } from '~/utils/helpers'
import type { UseQueryResult } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import { useTheme } from '@mui/material/styles'

export interface TimeSeriesData {
  label: string
  x: (string | number | null)[]
  y: (number | null)[]
  yLabel?: string
  lineColor?: string
}

interface XyTimeSeriesPlotProps {
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

const XyTimeSeriesPlot: React.FC<XyTimeSeriesPlotProps> = ({
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
    return localizedSeries.map((s) => {
      return {
        x: s.x,
        y: s.y,
        name: s.label,
        type: 'scatter',
        mode: 'lines',
        line: {
          width: 3,
        },
        yaxis: 'y',
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
      yaxis: {
        title: {
          text: 'Position [mm]',
          standoff: 5,
        },
        side: 'right',
        automargin: true,
        showgrid: true,
        showline: false,
        gridwidth: 0.4,
        gridcolor: gridColor,
        range: [-300, 300],
        fixedrange: true,
      },
      margin: { l: 20, r: 20, t: 20, b: 20 },
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
      doubleClick: 'reset',
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

export default XyTimeSeriesPlot
