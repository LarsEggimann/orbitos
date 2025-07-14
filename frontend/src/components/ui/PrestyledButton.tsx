import * as React from 'react'
import Button, { type ButtonProps } from '@mui/material/Button'
import Box from '@mui/material/Box'
import Tooltip from '@mui/material/Tooltip'
import type { Theme } from '@mui/material'

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

  const getBackgroundColor = (theme: Theme) => {
    if (color === 'primary') {
      return theme.palette.primary.main + '10'
    } else if (color === 'secondary') {
      return theme.palette.secondary.main + '10'
    } else if (color === 'warning') {
      return theme.palette.warning.main + '10'
    }
    return theme.palette.grey[100]
  }

  const getHoverBackgroundColor = (theme: Theme) => {
    if (color === 'primary') {
      return theme.palette.primary.main + '20'
    } else if (color === 'secondary') {
      return theme.palette.secondary.main + '20'
    } else if (color === 'warning') {
      return theme.palette.warning.main + '20'
    }
    return theme.palette.grey[200]
  }


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
        backgroundColor: getBackgroundColor,
        '&:hover': {
          backgroundColor: getHoverBackgroundColor,
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
