import React, { useEffect, useMemo, useState } from 'react'
import { fromTimestampToLocalizedString } from '~/utils/helpers'
import type { UseQueryResult } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import LoadingOverlay from '~/components/ui/LoadingOverlay'
import Plot from '~/components/plots/Plot'
import { useTheme } from '@mui/material/styles'

interface EMPlotProps {
  xData: number[]
  yData: number[]
  dataQuery?: UseQueryResult<any, Error>
  title?: string
  xAxisLabel?: string
  yAxisLabel?: string
  useTransitions?: boolean
  lineColor?: string
  currentToGreyConversionFactor?: number
  height?: string | number
}
type PlotlyFigure = {
  data: Plotly.Data[]
  layout: Partial<Plotly.Layout>
  frames?: Plotly.Frame[] | null
  config?: Partial<Plotly.Config>
}

const EMPlot: React.FC<EMPlotProps> = ({
  xData: x,
  yData: y,
  dataQuery,
  title,
  xAxisLabel = 'Time',
  yAxisLabel = 'Value',
  lineColor,
  currentToGreyConversionFactor = 1,
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

  const [localizedXAsStrings, setLocalizedXAsStrings] = useState<string[]>([])
  const [customData, setCustomData] = useState<[string, number, number][]>([])

  const hoverTemplate = '<b>Time:</b> %{customdata[0]}<br><b>Current:</b> %{customdata[1]} A<br><b>Dose Rate:</b> %{customdata[2]} Gy/s<extra></extra>'

  useEffect(() => {
    const currentLength = localizedXAsStrings.length
    if (x.length == currentLength + 1) {
      // compute only map the single new value (most common when we update via websocket)
      const newX = x.slice(currentLength) // new x values as strings with timezone information
      const newDates = newX.map((val) => fromTimestampToLocalizedString(val)) // convert to Date objects, defaults to local timezone

      setLocalizedXAsStrings((prev) => prev.concat(newDates))
      const newCustom = newDates.map(
        (datetime, i) =>
          [
            datetime.slice(0, -1), // remove the trailing 'Z' for display
            y[currentLength + i],
            y[currentLength + i] * currentToGreyConversionFactor,
          ] as [string, number, number],
      )
      setCustomData((prev) => prev.concat(newCustom))
    } else {
      // if there is not exactly one new value, we map the full x array new
      const datesAsLocalizedStrings = x.map((val) =>
        fromTimestampToLocalizedString(val),
      )
      setLocalizedXAsStrings(datesAsLocalizedStrings)
      setCustomData(
        datesAsLocalizedStrings.map(
          (dateStr, i) => [dateStr.slice(0, -1), y[i], y[i] * currentToGreyConversionFactor] as [string, number, number],
        ),
      )
    }
  }, [x, y, currentToGreyConversionFactor])

  const getPlotData = (xVals: string[], yVals: number[]): Plotly.Data[] => {
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
    }
  }

  const getFigure = (): PlotlyFigure => {
    return {
      data: getPlotData(localizedXAsStrings, y),
      layout: getLayout(),
      config: getConfig(),
    }
  }

  const [figure, setFigure] = useState<PlotlyFigure>(getFigure())

  useMemo(() => {
    const xVals = localizedXAsStrings
    const yVals = y
    if (xVals.length > 0) {
      setFigure((prevFigure) => ({
        ...prevFigure,
        data: getPlotData(xVals, yVals),
      }))
    }
  }, [localizedXAsStrings, y, textColor])

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

export default EMPlot
