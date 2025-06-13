import React, { useEffect, useMemo, useState } from 'react'
import Plot from 'react-plotly.js'
import * as Plotly from 'plotly.js-dist-min'

interface TimeSeriesChartProps {
  xData: string[]
  yData: number[]
  title?: string
  xAxisLabel?: string
  yAxisLabel?: string
  useTransitions?: boolean
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
  title,
  xAxisLabel = 'Time',
  yAxisLabel = 'Value',
  useTransitions = false,
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

  const [localizedXAsStrings, setLocalizedXAsStrings] = useState<string[]>([])
  const [customData, setCustomData] = useState<[string, number][]>([])

  // parse and format ISO string with microsecond precision in local timezone
  function fromatToLocalizedString(isoString: string): string {
    // Example input:  "2025-06-13T19:02:30.244260Z"
    // Example output: "2025-06-13T21:02:30.244260Z"
    const match = isoString.match(
      /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d{6})Z$/
    );
    if (!match) {
      throw new Error("Invalid ISO format with microseconds");
    }
    const [_, __, micro] = match;
    const date = new Date(isoString);
    // Get the local timezone offset in minutes
    const offsetMinutes = date.getTimezoneOffset();
    const localTimestamp = date.getTime() - offsetMinutes * 60 * 1000;
    const localDate = new Date(localTimestamp);
    // Build the adjusted ISO string with original microseconds
    const isoLocal = localDate.toISOString().replace(/\.\d{3}Z$/, '');
    const result = `${isoLocal}.${micro}Z`;
    return result;
  }
  
  useEffect(() => {
    const currentLength = localizedXAsStrings.length
    if (x.length == currentLength + 1) { // compute only map the single new value (most common when we update via websocket)
      const newX = x.slice(currentLength) // new x values as strings with timezone information
      const newDates = newX.map(val => fromatToLocalizedString(val)) // convert to Date objects, defaults to local timezone

      setLocalizedXAsStrings(prev => prev.concat(newDates))
      const newCustom = newDates.map((datetime, i) => [
        datetime.slice(0, -1), // remove the trailing 'Z' for display
        y[currentLength + i],
      ] as [string, number])
      setCustomData(prev => prev.concat(newCustom))

    } else { // if there is not exactly one new value, we map the full x array new
      const datesAsLocalizedStrings = x.map(val => fromatToLocalizedString(val))
      setLocalizedXAsStrings(datesAsLocalizedStrings)
      setCustomData(datesAsLocalizedStrings.map((dateStr, i) => [dateStr.slice(0, -1), y[i]] as [string, number]))
    }
  }, [x, y])

  const getPlotData = (
    xVals: string[],
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
      margin: { l: 60, r: 30, t: 0, b: 60 },
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
      data: getPlotData(localizedXAsStrings, y),
      layout: getLayout(),
      config: getConfig(),
    }
  }

  const [figure, setFigure] = useState<PlotlyFigure>(getFigure())

  useMemo(() => {
    const xVals = localizedXAsStrings
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
  }, [localizedXAsStrings, y, textColor])

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
