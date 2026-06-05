import ReactPlotly from 'react-plotly.js'

// somehow vite changed the way react-plotly is imported, so I added this extraction of the default export to make it work again
// if you use a Plot somewhere just import it from here
const Plot = (ReactPlotly as any).default || ReactPlotly

export default Plot
