import CircularProgress from '@mui/material/CircularProgress'
import Typography from '@mui/material/Typography'
import Card from '@mui/material/Card'
import Box from '@mui/material/Box'

import type { XyStagesState, StageState } from '~/generated'
import { replaceUnderscores } from '~/utils/helpers'

export const XyStagesStateDisplay = ({
  state = {} as XyStagesState,
}: {
  state?: XyStagesState
}) => {
  const {
    status = 'unknown',
    connection_status = 'unknown',
    error = 'unknown',
  } = state || {}

  const statusText = replaceUnderscores(status)
  const connectionStatusText = replaceUnderscores(connection_status)
  const errorText = error

  // Status color and spinner
  const isIdleOrUnknown =
    statusText.toLowerCase() === 'idle' ||
    statusText.toLowerCase() === 'unknown'
  const statusColor = isIdleOrUnknown ? 'default' : 'primary'

  // Connection color and spinner
  let connectionColor: 'success' | 'warning' | 'error' | 'default' = 'default'
  let showConnectionSpinner = false
  if (connectionStatusText.toLowerCase() === 'connected')
    connectionColor = 'success'
  else if (connectionStatusText.toLowerCase() === 'connecting') {
    connectionColor = 'warning'
    showConnectionSpinner = true
  } else connectionColor = 'error'

  // Error chip color
  const hasError = errorText && errorText.toLowerCase() !== 'no error'
  const errorColor = hasError ? 'error' : 'default'

  const xState = state?.x_state || {}
  const yState = state?.y_state || {}

  // Helper to format numbers
  const fmt = (val: number | null | undefined, digits = 3) =>
    typeof val === 'number' ? val.toFixed(digits) : '—'

  // Helper to format booleans
  const fmtBool = (val: boolean | null | undefined) =>
    val === true ? 'true' : val === false ? 'false' : '—'

  // Axis state display component
  const AxisState = ({ axis, state }: { axis: string; state: StageState }) => (
    <Box sx={{ minWidth: 220, flex: 1 }}>
      <Typography variant='body1' sx={{ mb: 1 }}>
        {axis} Axis - {state?.connection_status == 'connected' ? '🟢' : '🔴'}
      </Typography>
      <Typography variant='body2' color='text.secondary'>
        Position
      </Typography>
      <Typography variant='body1'>{fmt(state.position)}</Typography>
      <Typography variant='body2' color='text.secondary'>
        Moving
      </Typography>
      <Typography variant='body1'>{fmtBool(state.moving)}</Typography>
      <Typography variant='body2' color='text.secondary'>
        Enabled
      </Typography>
      <Typography variant='body1'>{fmtBool(state.enabled)}</Typography>
      <Typography variant='body2' color='text.secondary'>
        Axis Speed
      </Typography>
      <Typography variant='body1'>{fmt(state.axis_speed)}</Typography>
      <Typography variant='body2' color='text.secondary'>
        Device Number
      </Typography>
      <Typography variant='body1'>{state.device_number ?? '—'}</Typography>
      <Typography variant='body2' color='text.secondary'>
        Current Limit Errors
      </Typography>
      <Typography variant='body1'>{state.current_limit_errors ?? '—'}</Typography>
      <Typography variant='body2' color='text.secondary'>
        Axis Status
      </Typography>
      <Typography variant='body1'>
        {Array.isArray(state.axis_status)
          ? state.axis_status.join(', ')
          : state.axis_status ?? '—'}
      </Typography>
    </Box>
  )
  
  return (
    <Card sx={{ flexGrow: 1, mb: 1, p: 2 }}>
      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          gap: 4,
        }}
      >
        
        {/* General connection/status/error info */}
        <Box sx={{ minWidth: 220, flexShrink: 0 }}>
          <Typography variant='body1' color='text.secondary' sx={{ mt: 2 }}>
            Status
          </Typography>
          <Typography
            variant='body1'
            color={statusColor}
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            {!isIdleOrUnknown && <CircularProgress size={14} sx={{ mr: 1 }} />}
            {statusText}
          </Typography>
          <Typography variant='body1' color='text.secondary' sx={{ mt: 2 }}>
            Error
          </Typography>
          <Typography
            variant='body1'
            color={errorColor}
            sx={{ wordBreak: 'break-word' }}
          >
            {hasError ? errorText : 'no error reported'}
          </Typography>
        </Box>

        {/* X and Y axis info side by side */}
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'row',
            gap: 2,
            flexGrow: 1,
            flexWrap: 'wrap',
          }}
        >
          <AxisState axis='X' state={xState} />
          <AxisState axis='Y' state={yState} />
        </Box>
      </Box>
    </Card>
  )
}
