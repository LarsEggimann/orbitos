import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import { replaceUnderscores } from '~/utils/helpers';
import { BaseState } from '~/generated';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Card from '@mui/material/Card';

export const DeviceStateDisplay = ({ state = {} as BaseState }: { state?: BaseState }) => {
  const {
    device_name = 'unknown',
    status = 'unknown',
    connection_status = 'unknown',
    error = 'unknown',
  } = state || {};

  const deviceName = replaceUnderscores(device_name)?.charAt(0).toUpperCase() + replaceUnderscores(device_name)?.slice(1);
  const statusText = replaceUnderscores(status);
  const connectionStatusText = replaceUnderscores(connection_status);
  const errorText = error;

  // Status color and spinner
  const isIdleOrUnknown = statusText.toLowerCase() === 'idle' || statusText.toLowerCase() === 'unknown';
  const statusColor = isIdleOrUnknown ? 'default' : 'primary';

  // Connection color and spinner
  let connectionColor: 'success' | 'warning' | 'error' | 'default' = 'default';
  let showConnectionSpinner = false;
  if (connectionStatusText.toLowerCase() === 'connected') connectionColor = 'success';
  else if (connectionStatusText.toLowerCase() === 'connecting') {
    connectionColor = 'warning';
    showConnectionSpinner = true;
  } else connectionColor = 'error';

  // Error chip color
  const hasError = errorText && errorText.toLowerCase() !== 'no error';
  const errorColor = hasError ? 'error' : 'default';

  return (
    <Card sx={{ flexGrow: 1, mb: 1, p: 2 }}>
      <Typography variant="h6">{deviceName} State</Typography>
      <Table sx={{ minWidth: 300 }}>
        <TableBody>
          <TableRow>
            <TableCell sx={{ border: 0, pl: 0, pr: 2, width: 200 }}>
              <Typography>Status:</Typography>
            </TableCell>
            <TableCell sx={{ border: 0, pl: 0 }}>
              <Typography
                color={statusColor}
                sx={{ display: 'flex', alignItems: 'center' }}>
                {!isIdleOrUnknown && (
                      <CircularProgress size={16} sx={{ mr: 2 }} />
                    )}
                    {statusText}
              </Typography>
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell sx={{ border: 0, pl: 0, pr: 2, width: 120 }}>
              <Typography>Connection:</Typography>
            </TableCell>
            <TableCell sx={{ border: 0, pl: 0 }}>
              <Typography
                color={connectionColor}
                sx={{ display: 'flex', alignItems: 'center' }}>
                    {showConnectionSpinner && (
                      <CircularProgress size={16} sx={{ mr: 2 }} />
                    )}
                    {connectionStatusText}
                  </Typography>
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell sx={{ border: 0, pl: 0, pr: 2, width: 120 }}>
              <Typography>Error:</Typography>
            </TableCell>
            <TableCell sx={{ border: 0, pl: 0 }}>
              <Typography
                color={errorColor}
                sx={{ wordBreak: 'break-word' }}>
                {hasError ? errorText : 'no error reported'}
              </Typography>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </Card>
  );
};

export const DeviceSettingsDisplay = ({ settings }: { settings: any }) => (
  <Box sx={{ flexGrow: 1, mb: 2 }}>
    <Typography variant="h6">Settings</Typography>
    <Paper sx={{ p: 2, backgroundColor: '#f5f5f5' }}>
      <pre style={{ margin: 0 }}>{JSON.stringify(settings, null, 2)}</pre>
    </Paper>
  </Box>
);

