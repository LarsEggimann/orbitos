import React from 'react';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import SettingsBrightnessIcon from '@mui/icons-material/SettingsBrightness';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import { useThemeMode } from '../../provider/ThemeProvider';

export const ThemeToggleButton = () => {
  const { mode, setMode, resolvedMode } = useThemeMode();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };

  const icon = mode === 'system' ? <SettingsBrightnessIcon /> : (mode === 'dark' ? <Brightness4Icon /> : <Brightness7Icon />);
  const label = mode === 'system' ? `System (${resolvedMode})` : mode.charAt(0).toUpperCase() + mode.slice(1);

  return (
    <>
      <Tooltip title={`Theme: ${label}`}>
        <IconButton color="inherit" onClick={handleClick} size="large" aria-label="toggle theme">
          {icon}
        </IconButton>
      </Tooltip>
      <Menu anchorEl={anchorEl} open={open} onClose={handleClose}>
        <MenuItem selected={mode === 'system'} onClick={() => { setMode('system'); handleClose(); }}>
          <ListItemIcon><SettingsBrightnessIcon /></ListItemIcon>
          <ListItemText>System</ListItemText>
        </MenuItem>
        <MenuItem selected={mode === 'light'} onClick={() => { setMode('light'); handleClose(); }}>
          <ListItemIcon><Brightness7Icon /></ListItemIcon>
          <ListItemText>Light</ListItemText>
        </MenuItem>
        <MenuItem selected={mode === 'dark'} onClick={() => { setMode('dark'); handleClose(); }}>
          <ListItemIcon><Brightness4Icon /></ListItemIcon>
          <ListItemText>Dark</ListItemText>
        </MenuItem>
      </Menu>
    </>
  );
};
