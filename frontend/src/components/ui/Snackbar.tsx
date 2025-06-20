import * as React from 'react'
import Snackbar, { SnackbarProps } from '@mui/material/Snackbar'
import Alert, { AlertProps } from '@mui/material/Alert'

export type ReusableSnackbarProps = {
  openState: [boolean, React.Dispatch<React.SetStateAction<boolean>>]
  alertProps?: {
    message?: string
    severity?: AlertProps['severity']
  } & AlertProps
} & SnackbarProps

const ReusableSnackbar: React.FC<ReusableSnackbarProps> = ({
  openState,
  alertProps = {
    message: '',
    severity: 'success',
  },
  children,
  ...rest
}) => {
  const [open, setOpen] = openState

  return (
    <>
      <Snackbar
        open={open}
        autoHideDuration={4000}
        onClose={() => setOpen(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        {...rest}
      >
        <Alert
          onClose={() => setOpen(false)}
          severity={alertProps.severity}
          sx={{ width: '100%' }}
        >
          {alertProps.message || children}
        </Alert>
      </Snackbar>
    </>
  )
}

export default ReusableSnackbar
