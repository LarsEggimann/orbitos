import React, { useEffect, useState } from 'react'
import Plot from 'react-plotly.js'
import Box from '@mui/material/Box'
import { useTheme } from '@mui/material/styles'

interface XyPositionPlotProps {
    xPosition?: number | null
    yPosition?: number | null
    width?: string | number
    height?: string | number
}

type PlotlyFigure = {
    data: Plotly.Data[]
    layout: Partial<Plotly.Layout>
    frames?: Plotly.Frame[] | null
    config?: Partial<Plotly.Config>
}

const XyPositionPlot: React.FC<XyPositionPlotProps> = ({
    xPosition = 0,
    yPosition = 0,
    width = '800px',
    height = '600px',
}) => {
    const muiTheme = useTheme()

    const textColor = muiTheme.palette.text.primary
    const gridColor = muiTheme.palette.divider
    const bgColor = 'transparent'

    // Stage rectangle size (in mm)
    const stageWidth = 300
    const stageHeight = 300

    const getPlotData = (): Plotly.Data[] => {
        const x = xPosition || 0
        const y = yPosition || 0

        // Create rectangle coordinates for the stage
        const stageX = [
            x - stageWidth / 2,
            x + stageWidth / 2,
            x + stageWidth / 2,
            x - stageWidth / 2,
            x - stageWidth / 2,
        ]
        const stageY = [
            y - stageHeight / 2,
            y - stageHeight / 2,
            y + stageHeight / 2,
            y + stageHeight / 2,
            y - stageHeight / 2,
        ]

        return [
            // Stage rectangle
            {
                x: stageX,
                y: stageY,
                type: 'scatter',
                mode: 'lines',
                fill: 'toself',
                fillcolor: 'rgba(128, 128, 128, 0.6)',
                line: {
                    color: 'rgba(128, 128, 128, 0)',
                    width: 2,
                },
                name: 'Stage',
                showlegend: true,
            },
            // Center cross
            {
                x: [0],
                y: [0],
                type: 'scatter',
                mode: 'markers',
                marker: {
                    symbol: 'x',
                    size: 15,
                    color: muiTheme.palette.primary.main,
                },
                line: {
                    color: textColor,
                    width: 2,
                },
                name: 'Beam Position',
                showlegend: true,
                hoverinfo: 'skip',
            },
        ]
    }

    const getLayout = (): Partial<Plotly.Layout> => {
        const x = xPosition || 0
        const y = yPosition || 0
        
        return {
            font: {
                color: textColor,
                size: 14,
            },
            autosize: true,
            paper_bgcolor: bgColor,
            plot_bgcolor: bgColor,
            xaxis: {
                title: {
                    text: 'X Position [mm]',
                    standoff: 5,
                },
                automargin: true,
                showgrid: true,
                showline: false,
                gridwidth: 0.4,
                gridcolor: gridColor,
                range: [-300, 300],
                fixedrange: true,
            },
            yaxis: {
                title: {
                    text: 'Y Position [mm]',
                    standoff: 5,
                },
                automargin: true,
                showgrid: true,
                showline: false,
                gridwidth: 0.4,
                gridcolor: gridColor,
                range: [-300, 300],
                fixedrange: true,
            },
            margin: { l: 20, r: 0, t: 20, b: 20 },
            showlegend: true,
            annotations: [
                {
                    text: `Position: X = ${x.toFixed(2)} mm, Y = ${y.toFixed(2)} mm`,
                    xref: 'paper',
                    yref: 'paper',
                    x: 0.80,
                    y: 0.10,
                    xanchor: 'left',
                    yanchor: 'top',
                    showarrow: false,
                    font: {
                        size: 14,
                        color: textColor,
                    },
                    bgcolor: 'transparent',
                    bordercolor: gridColor,
                    borderwidth: 1,
                    borderpad: 8,
                },
            ],
        }
    }

    const getConfig = (): Partial<Plotly.Config> => {
        return {
            responsive: true,
            displaylogo: false,
            displayModeBar: false,
            staticPlot: true,
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

    useEffect(() => {
        setFigure(getFigure())
    }, [xPosition, yPosition, muiTheme, textColor])

    return (
        <Box sx={{ position: 'relative', width: width, height: height }}>
            <Box
                sx={{
                    transition: 'opacity 0.2s',
                    width: width,
                    height: height,
                }}
            >
                <Plot
                    data={figure.data}
                    layout={figure.layout}
                    frames={figure.frames || []}
                    config={figure.config}
                    useResizeHandler={true}
                    style={{ width: width, height: height }}
                />
            </Box>
        </Box>
    )
}

export default XyPositionPlot
