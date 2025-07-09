import React, {
  createContext,
  type PropsWithChildren,
  useCallback,
  useContext,
} from 'react'
import { SnackbarProvider as NotistackProvider, useSnackbar, type VariantType } from 'notistack'

export type SnackbarSeverity = 'success' | 'error' | 'warning' | 'info'

export type SnackbarContextType = {
  openSnackbar: (msg: string, severity?: SnackbarSeverity) => void
  // Legacy support for existing components
  snackbar: { open: boolean; msg: string; severity: SnackbarSeverity }
  closeSnackbar: () => void
}

const SnackbarContext = createContext<SnackbarContextType | undefined>(
  undefined,
)

// Wrapper component that provides the custom snackbar context
function SnackbarContextProvider({ children }: PropsWithChildren<any>) {
  const { enqueueSnackbar } = useSnackbar()

  const openSnackbar = useCallback(
    (msg: string, severity: SnackbarSeverity = 'success') => {
      enqueueSnackbar(msg, { variant: severity as VariantType })
    },
    [enqueueSnackbar],
  )

  // Legacy support - return empty values for backward compatibility
  const legacySnackbar = {
    open: false,
    msg: '',
    severity: 'success' as SnackbarSeverity,
  }

  const closeSnackbar = useCallback(() => {
    // Notistack handles closing automatically, this is for legacy support
  }, [])

  return React.createElement(
    SnackbarContext.Provider,
    { value: { openSnackbar, snackbar: legacySnackbar, closeSnackbar } },
    children,
  )
}

// Main provider that wraps both notistack and our custom context
export function SnackbarProvider({ children }: PropsWithChildren<any>) {
  return React.createElement(
    NotistackProvider,
    { 
      maxSnack: 5,
      anchorOrigin: { vertical: 'top', horizontal: 'right' },
      autoHideDuration: 4000,
    },
    React.createElement(SnackbarContextProvider, null, children)
  )
}

export function useSnackbarContext() {
  const ctx = useContext(SnackbarContext)
  if (!ctx)
    throw new Error('useSnackbarContext must be used within a SnackbarProvider')
  return ctx
}
