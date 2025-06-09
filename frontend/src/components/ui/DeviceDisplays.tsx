import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';

export const DeviceStateDisplay = ({ state }: { state: any }) => (
  <Card sx={{ mb: 2 }}>
    <CardContent>
      <Typography variant="h6">Device State</Typography>
      <pre style={{ margin: 0 }}>{JSON.stringify(state, null, 2)}</pre>
    </CardContent>
  </Card>
);

export const DeviceSettingsDisplay = ({ settings }: { settings: any }) => (
  <Card sx={{ mb: 2 }}>
    <CardContent>
      <Typography variant="h6">Settings</Typography>
      <pre style={{ margin: 0 }}>{JSON.stringify(settings, null, 2)}</pre>
    </CardContent>
  </Card>
);

