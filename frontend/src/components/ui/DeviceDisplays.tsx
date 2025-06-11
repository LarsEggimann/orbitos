import * as React from 'react';
import { styled } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Grid from '@mui/material/Grid';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import { replaceUnderscores } from '~/utils/helpers';
import { BaseState } from '~/generated';
import Stack from '@mui/material/Stack';

export const DeviceStateDisplay = ({ state = {} as BaseState }: { state?: BaseState }) => {
  // Destructure with defaults
  const {
    device_id = 'unknown',
    status = 'unknown',
    connection_status = 'unknown',
    error = 'unknown',
  } = state || {};

  const deviceId = replaceUnderscores(device_id)?.charAt(0).toUpperCase() + replaceUnderscores(device_id)?.slice(1);
  const statusText = replaceUnderscores(status);
  const connectionStatusText = replaceUnderscores(connection_status);
  const errorText = error;

  // Status color and spinner
  const isIdle = statusText.toLowerCase() === 'idle';
  const statusColor = isIdle ? 'default' : 'primary';

  // Connection chip color and spinner
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
    <Box sx={{ flexGrow: 1, mb: 2 }}>
      <Typography variant="h6" gutterBottom>{deviceId} State</Typography>

      <Stack direction={'column'} spacing={2} sx={{ mb: 2 }}>


        <Stack
                direction="row"
                sx={{ alignItems: 'center', gap: 2 }}
                >
                <Typography>Status: </Typography>
                <Chip
                label={
                  <span style={{ display: 'flex', alignItems: 'center' }}>
                    {!isIdle && (
                      <CircularProgress size={16} sx={{ mr: 2 }} />
                    )}
                    {statusText}
                  </span>
                }
                color={statusColor}
                variant="outlined"
                sx={{ minWidth: 120 }}
                />
        </Stack>
        <Stack
              direction="row"
              sx={{ alignItems: 'center', gap: 2 }}
              >
              <Typography>Connection: </Typography>
              <Chip
              label={
                <span style={{ display: 'flex', alignItems: 'center' }}>
                  {showConnectionSpinner && (
                    <CircularProgress size={16} sx={{ mr: 1 }} />
                  )}
                  {connectionStatusText}
                </span>
              }
              color={connectionColor}
              variant="outlined"
              sx={{ minWidth: 120 }}
            />
      </Stack>

        <Stack
              direction="row"
              sx={{ alignItems: 'center', gap: 2 }}
              >
              <Typography>Error: </Typography>
              <Chip
                label={errorText}
                color={errorColor}
                variant="outlined"
                sx={{
                  bgcolor: hasError ? '#ffebee' : undefined,
                  color: hasError ? 'red' : undefined,
                  minWidth: 120,
                }}
              />
        </Stack>

      </Stack>
      
    </Box>
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

