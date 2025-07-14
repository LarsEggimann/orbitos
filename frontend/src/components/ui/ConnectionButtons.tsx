import React from 'react'
import Box from '@mui/material/Box'
import UsbIcon from '@mui/icons-material/Usb';
import UsbOffIcon from '@mui/icons-material/UsbOff';
import RotateLeftIcon from '@mui/icons-material/RotateLeft';
import ExecQueryButton from './ExecQueryButton'

export type ConnectionButtonsProps = {
  connectionStatus?: 'connected' | 'disconnected' | string
  onConnect: () => Promise<any>
  onDisconnect: () => Promise<any>
  connectDisabled?: boolean
  disconnectDisabled?: boolean
  additionalConnectValidation?: boolean
  connectTooltipText?: string
  disconnectTooltipText?: string
  showResetError?: boolean
  onResetError?: () => Promise<any>
  resetErrorText?: string
}

const ConnectionButtons: React.FC<ConnectionButtonsProps> = ({
  connectionStatus,
  onConnect,
  onDisconnect,
  connectDisabled = false,
  disconnectDisabled = false,
  additionalConnectValidation = true,
  connectTooltipText = 'Connect to device',
  disconnectTooltipText = 'Disconnect from device',
  showResetError = false,
  onResetError,
  resetErrorText = 'Reset Error',
}) => {

  return (
    <>
      <ExecQueryButton
        onClick={onConnect}
        tooltip={connectTooltipText}
        disabled={connectDisabled || !additionalConnectValidation}
      >
        <UsbIcon />
      </ExecQueryButton>
      <ExecQueryButton
        onClick={onDisconnect}
        tooltip={disconnectTooltipText}
        disabled={disconnectDisabled}
        color='warning'
      >
        <UsbOffIcon />
      </ExecQueryButton>
      <Box flexGrow={1}></Box>
      {showResetError && onResetError && (
        <ExecQueryButton
        onClick={onResetError}
        startIcon={<RotateLeftIcon />}>
          {resetErrorText}
        </ExecQueryButton>
      )}
    </>
  )
}

export default ConnectionButtons
