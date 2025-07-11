import * as React from 'react'
import Button, { type ButtonProps } from '@mui/material/Button'
import Box from '@mui/material/Box'

export type PrestyledButtonProps = ButtonProps

const PrestyledButton: React.FC<PrestyledButtonProps> = ({
  variant = 'text',
  color = 'primary',
  sx,
  children,
  ...rest
}) => {
  return (
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
      <Box sx={{ mt: 0.5}}>
        {children}
      </Box>
    </Button>
  )
}

export default PrestyledButton
