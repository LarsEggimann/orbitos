import React, { useEffect, useMemo, useState } from 'react'
import Plot from 'react-plotly.js'
import type { UseQueryResult } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import LoadingOverlay from '~/components/ui/LoadingOverlay'
import { useTheme } from '@mui/material/styles'

interface ScatterPlotProps {
  xData: number[]
  yData: number[]
  dataQuery?: UseQueryResult<any, Error>
  title?: string
  xAxisLabel?: string
  yAxisLabel?: string
  useTransitions?: boolean
  lineColor?: string
  height?: string | number
}
type PlotlyFigure = {
  data: Plotly.Data[]
  layout: Partial<Plotly.Layout>
  frames?: Plotly.Frame[] | null
  config?: Partial<Plotly.Config>
}

const ScatterPlot: React.FC<ScatterPlotProps> = ({
  xData: x,
  yData: y,
  dataQuery,
  title,
  xAxisLabel = 'x',
  yAxisLabel = 'y',
  lineColor,
  height = '600px',
}) => {
  const muiTheme = useTheme()
  const isDark = muiTheme.palette.mode === 'dark'

  const textColor = muiTheme.palette.text.primary
  const gridColor = muiTheme.palette.divider
  const defaultLineColor = isDark
    ? muiTheme.palette.primary.main
    : muiTheme.palette.primary.main
  const tooltipBgColor = muiTheme.palette.background.paper
  const tooltipBorderColor = muiTheme.palette.divider
  const bgColor = 'transparent'

  const finalLineColor = lineColor || defaultLineColor


  const getPlotData = (xVals: number[], yVals: number[]): Plotly.Data[] => {
    return [
      {
        x: xVals,
        y: yVals,
        type: 'scatter',
        mode: 'markers',
        marker: {
          size: 4,
          color: finalLineColor,

        },
        hoverlabel: {
          bgcolor: tooltipBgColor,
          bordercolor: tooltipBorderColor,
          font: {
            family: 'Inter, sans-serif',
            size: 12,
            color: textColor,
          },
        },
      },
    ]
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
          text: yAxisLabel,
          standoff: 5,
        },
        automargin: true,
        showgrid: true,
        showline: false,
        gridwidth: 0.4,
        gridcolor: gridColor,
      },
      margin: { l: 20, r: 20, t: 60, b: 20 },
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
      data: getPlotData(x, y),
      layout: getLayout(),
      config: getConfig(),
    }
  }

  const [figure, setFigure] = useState<PlotlyFigure>(getFigure())

  useMemo(() => {
    const xVals = x
    const yVals = y

    if (xVals.length > 0) {
      setFigure((prevFigure) => ({
        ...prevFigure,
        data: getPlotData(xVals, yVals),
      }))
    }
  }, [x, y, textColor])

  // reload figure when dataQuery changes or muiTheme changes
  useEffect(() => {
    console.log('Data query changed, reloading figure')
    setFigure(getFigure())
  }, [dataQuery?.data, muiTheme])

  return (
    <Box sx={{ position: 'relative', width: '100%', height: height }}>
      <LoadingOverlay query={dataQuery} height={height} />
      <Box
        sx={{
          opacity: dataQuery?.isLoading || dataQuery?.isFetching ? 0.3 : 1,
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

export default ScatterPlot
