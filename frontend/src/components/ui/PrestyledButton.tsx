import * as React from 'react'
import Button, { type ButtonProps } from '@mui/material/Button'
import Box from '@mui/material/Box'
import Tooltip from '@mui/material/Tooltip'

export type PrestyledButtonProps = ButtonProps & {
  tooltip?: string
}

const PrestyledButton: React.FC<PrestyledButtonProps> = ({
  variant = 'text',
  color = 'primary',
  sx,
  children,
  tooltip,
  ...rest
}) => {
  const button = (
    <Button
      variant={variant}
      color={color}
      sx={{
        textTransform: 'none',
        display: 'flex',
        alignItems: 'center',
        textAlign: 'center',
        border: 'none',
        backgroundColor: (theme) =>
          color === 'primary'
            ? theme.palette.primary.main + '10'
            : theme.palette.grey[100],
        '&:hover': {
          backgroundColor: (theme) =>
            color === 'primary'
              ? theme.palette.primary.main + '20'
              : theme.palette.grey[200],
          border: 'none',
        },
        ...sx,
      }}
      {...rest}
    >
      <Box sx={{ 
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {children}
      </Box>
    </Button>
  )

  if (tooltip) {
    return <Tooltip title={tooltip}>{button}</Tooltip>
  }

  return button
}

export default PrestyledButton
