import React, { useEffect, useMemo, useState } from 'react'
import Plot from 'react-plotly.js'
import type { UseQueryResult } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import LoadingOverlay from '~/components/ui/LoadingOverlay'
import { useTheme } from '@mui/material/styles'

interface CwPosVeloPlotProps {
  xData: number[]
  yData: number[]
  dataQuery?: UseQueryResult<any, Error>
  title?: string
  xAxisLabel?: string
  yAxisLabel?: string
  useTransitions?: boolean
  lineColor?: string
  hoverTemplate?: string
  height?: string | number
}
type PlotlyFigure = {
  data: Plotly.Data[]
  layout: Partial<Plotly.Layout>
  frames?: Plotly.Frame[] | null
  config?: Partial<Plotly.Config>
}

const CwPosVeloPlot: React.FC<CwPosVeloPlotProps> = ({
  xData: x,
  yData: y,
  dataQuery,
  title,
  xAxisLabel = 'Time',
  yAxisLabel = 'Value',
  hoverTemplate = '<b>X:</b> %{x}<br><b>Y:</b> %{y}<extra></extra>',
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

  const [customData, setCustomData] = useState<[number, number][]>([])

  useEffect(() => {
    const currentLength = customData.length
    if (x.length == currentLength + 1) {
      // compute only map the single new value (most common when we update via websocket)
      const newX = x.slice(currentLength) // new x values as strings with timezone information
      const newTuples = newX.map(
        (x_i, i) => [x_i, y[currentLength + i]] as [number, number],
      )

      setCustomData((prev) => prev.concat(newTuples))
    } else {
      // if there is not exactly one new value, we map the full x array new
      setCustomData(x.map((x_i, i) => [x_i, y[i]] as [number, number]))
    }
  }, [x, y])

  const getPlotData = (xVals: number[], yVals: number[]): Plotly.Data[] => {
    return [
      {
        x: xVals,
        y: yVals,
        type: 'scatter',
        mode: 'lines',
        line: {
          color: finalLineColor,
          // shape: 'spline',
          // smoothing: 0.5,
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
        customdata: customData,
        hovertemplate: hoverTemplate,
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
      margin: { l: 60, r: 30, t: 0, b: 60 },
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

    // const currentLayout = getLayout()

    if (xVals.length > 0) {
      setFigure((prevFigure) => ({
        ...prevFigure,
        data: getPlotData(xVals, yVals),
        // layout: newLayout,
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

export default CwPosVeloPlot
