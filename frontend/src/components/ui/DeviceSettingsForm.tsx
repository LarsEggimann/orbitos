import React, { useMemo, useCallback } from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Typography from '@mui/material/Typography';
import type { AxiosError, AxiosResponse } from 'axios';
import Snackbar from './Snackbar';
import { isAxiosError } from '~/utils/helpers';

// Exclude these keys from settings
const EXCLUDED_KEYS = ['function', 'trigger_bypass'];
// Settings that should be ON/OFF dropdowns
const ON_OFF_KEYS = ['current_range_auto', 'aperture_auto'];

export function DeviceSettingsForm({ settings, onChange, disabled }: {
  settings: Record<string, any>,
  onChange: (key: string, value: any) => Promise<AxiosResponse<any> | AxiosError<any> | void>,
  disabled?: boolean
}) {
  // Memoize keys to avoid unnecessary re-renders
  const keys = useMemo(() => Object.keys(settings || {}).filter(
    k => !EXCLUDED_KEYS.includes(k)
  ), [settings]);

  const [snackbar, setSnackbar] = React.useState<{ open: boolean, msg: string, severity: 'success' | 'error' }>({ open: false, msg: '', severity: 'success' });

  const handleChange = useCallback(async (key: string, value: any) => {
    // Convert number fields
    let val = value;
    if (typeof settings[key] === 'number' && value !== '') {
      val = Number(value);
    }

    try {
      const result = await onChange(key, val);
            if (isAxiosError(result)) {
                // Error response from axios
                const msg = result.response?.data?.message || result.message || 'An error occurred';
                const additionalInfo = result.response?.data?.detail || '';
                setSnackbar({ open: true, msg: msg + (additionalInfo ? `: ${additionalInfo}` : ''), severity: 'error' });
            } else if (result && typeof result === 'object' && 'data' in result && result.data && typeof result.data === 'object' && 'message' in result.data) {
                // Success response
                const msg = (result.data as any).message;
                if (typeof msg === 'string') {
                    setSnackbar({ open: true, msg, severity: 'success' });
                }
            }
        } catch (err: any) {
            // Network or unexpected error
            const msg = err?.response?.data?.message || err?.message || 'An error occurred';
            setSnackbar({ open: true, msg, severity: 'error' });
        }
  }, [onChange, settings]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {keys.length === 0 && <Typography color="text.secondary">No settings available.</Typography>}
      {keys.map(key => {
        const value = settings[key];
        if (ON_OFF_KEYS.includes(key)) {
          return (
            <TextField
              key={key}
              select
              label={key.replace(/_/g, ' ')}
              value={value === 'ON' ? 'ON' : value === 'OFF' ? 'OFF' : ''}
              onChange={e => handleChange(key, e.target.value)}
              disabled={disabled}
            >
              <MenuItem value="ON">ON</MenuItem>
              <MenuItem value="OFF">OFF</MenuItem>
            </TextField>
          );
        }
        return (
          <TextField
            key={key}
            label={key.replace(/_/g, ' ')}
            value={value ?? ''}
            onChange={e => handleChange(key, e.target.value)}
            disabled={disabled}
            type={typeof value === 'number' ? 'number' : 'text'}
          />
        );
      })}
      <Snackbar
        openState={[snackbar.open, (open) => setSnackbar(prev => ({ ...prev, open: open as boolean }))]}
        alertProps={{
          message: snackbar.msg,
          severity: snackbar.severity
        }}

      />
    </Box>
  );
}
