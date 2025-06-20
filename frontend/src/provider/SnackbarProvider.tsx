import React, {
  createContext,
  PropsWithChildren,
  useCallback,
  useContext,
  useState,
} from 'react'

export type SnackbarSeverity = 'success' | 'error'

export type SnackbarState = {
  open: boolean
  msg: string
  severity: SnackbarSeverity
}

export type SnackbarContextType = {
  snackbar: SnackbarState
  openSnackbar: (msg: string, severity?: SnackbarSeverity) => void
  closeSnackbar: () => void
}

const SnackbarContext = createContext<SnackbarContextType | undefined>(
  undefined,
)

export function SnackbarProvider({ children }: PropsWithChildren<any>) {
  const [snackbar, setSnackbar] = useState<SnackbarState>({
    open: false,
    msg: '',
    severity: 'success',
  })

  const openSnackbar = useCallback(
    (msg: string, severity: SnackbarSeverity = 'success') => {
      setSnackbar({ open: true, msg, severity })
    },
    [],
  )

  const closeSnackbar = useCallback(() => {
    setSnackbar((prev) => ({ ...prev, open: false }))
  }, [])

  return React.createElement(
    SnackbarContext.Provider,
    { value: { snackbar, openSnackbar, closeSnackbar } },
    children,
  )
}

export function useSnackbarContext() {
  const ctx = useContext(SnackbarContext)
  if (!ctx)
    throw new Error('useSnackbarContext must be used within a SnackbarProvider')
  return ctx
}
