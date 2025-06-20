import * as React from 'react'
import Button, { ButtonProps } from '@mui/material/Button'

export type PrestyledButtonProps = ButtonProps

const PrestyledButton: React.FC<PrestyledButtonProps> = ({
  variant = 'outlined',
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
        ...sx,
      }}
      {...rest}
    >
      {children}
    </Button>
  )
}

export default PrestyledButton
