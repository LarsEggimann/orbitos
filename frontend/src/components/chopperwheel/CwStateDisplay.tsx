import CircularProgress from '@mui/material/CircularProgress'
import Grid from '@mui/material/Grid'
import Typography from '@mui/material/Typography'
import Card from '@mui/material/Card'

import type { CwState } from '~/generated'
import { replaceUnderscores } from '~/utils/helpers'

export const CwStateDisplay = ({
  state = {} as CwState,
}: {
  state?: CwState
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

  return (
    <Card sx={{ flexGrow: 1, mb: 1, p: 2 }}>
      <Grid container spacing={4}>
        <Grid sx={{ minWidth: 120 }}>
          <Typography variant='body1' color='text.secondary'>
            Connection
          </Typography>
          <Typography
            variant='body1'
            color={connectionColor}
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            {showConnectionSpinner && (
              <CircularProgress size={14} sx={{ mr: 1 }} />
            )}
            {connectionStatusText}
          </Typography>
        </Grid>
        <Grid sx={{ minWidth: 350 }}>
          <Typography variant='body1' color='text.secondary'>
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
        </Grid>
        <Grid sx={{ minWidth: 150 }}>
          <Typography variant='body1' color='text.secondary'>
            Error
          </Typography>
          <Typography
            variant='body1'
            color={errorColor}
            sx={{ wordBreak: 'break-word' }}
          >
            {hasError ? errorText : 'no error reported'}
          </Typography>
        </Grid>
      </Grid>
    </Card>
  )
}
