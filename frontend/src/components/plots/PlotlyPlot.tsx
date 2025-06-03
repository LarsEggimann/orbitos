import React, { useMemo, useState } from 'react'
import Plot from 'react-plotly.js'
import * as Plotly from 'plotly.js-dist-min'

interface TimeSeriesChartProps {
  xData: number[] | string[]
  yData: number[]
  title?: string
  xAxisLabel?: string
  yAxisLabel?: string
  useTrnsitions?: boolean
  animationDuration?: number // duration in milliseconds
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

const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({
  xData: x,
  yData: y,
  title = 'Time Series Chart',
  xAxisLabel = 'Time',
  yAxisLabel = 'Value',
  useTrnsitions: useTransitions = false,
  animationDuration = 1000,
  hoverTemplate = '<b>X:</b> %{x}<br><b>Y:</b> %{y}<extra></extra>',
  lineColor,
  height = '600px',
}) => {
  const textColor = '#1A202C'
  const gridColor = '#CBD5E0'
  const defaultLineColor = 'rgba(234, 104, 104, 0.9)'
  
  const tooltipBgColor = 'rgba(255, 255, 255, 0.9)'

  const tooltipBorderColor = '#CBD5E0'
  const bgColor = 'transparent'

  const finalLineColor = lineColor || defaultLineColor

  const customData = x.map((i, j) => [new Date(i).toLocaleTimeString(), y[j]])

  const getPlotData = (
    xVals: number[] | string[],
    yVals: number[],
  ): Plotly.Data[] => {
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
      margin: { l: 60, r: 30, t: 35, b: 60 },
      transition: useTransitions
        ? {
            duration: animationDuration,
            easing: 'cubic-in-out',
          }
        : undefined,
    }
  }

  const getConfig = (): Partial<Plotly.Config> => {
    return {
      responsive: true,
      displaylogo: false,
      displayModeBar: false,
      toImageButtonOptions: {
        format: 'png',
        filename: 'chart_export',
      },
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

    const currentLayout = getLayout()

    if (xVals.length > 0) {
      const newLayout: Partial<Plotly.Layout> = {
        ...currentLayout,
        xaxis: {
          ...currentLayout.xaxis,
          range: [xVals[0], xVals[xVals.length - 1]], // update range to fit data
        },
        yaxis: {
          ...currentLayout.yaxis,
          range: [Math.min(...yVals), Math.max(...yVals)], // update range to fit data
        },
      }

      setFigure((prevFigure) => ({
        ...prevFigure,
        data: getPlotData(xVals, yVals),
        layout: newLayout,
      }))
    }
  }, [x, y, textColor])

  return (
    <div>
      <Plot
        data={figure.data}
        layout={figure.layout}
        frames={figure.frames || []}
        config={figure.config}
        useResizeHandler={true}
        style={{ width: '100%', height: height }}
      />
    </div>
  )
}

export default TimeSeriesChart
