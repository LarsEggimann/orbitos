import { ReactNode } from 'react'
import { Box } from '@mui/material'

import { AppProvider, DashboardLayout, type Navigation } from '@toolpad/core'
import { MdElectricBolt } from 'react-icons/md'
import { FaHome } from 'react-icons/fa'

import Logo from '~/components/ui/Logo'
import {
  SnackbarProvider,
  useSnackbarContext,
} from '~/provider/SnackbarProvider'
import Snackbar from '~/components/ui/Snackbar'

const NAVIGATION: Navigation = [
  {
    segment: '/',
    title: 'Home',
    icon: <FaHome />,
  },
  {
    segment: 'electrometer/1',
    title: 'Electrometer 1',
    icon: <MdElectricBolt />,
  },
]

type LayoutProps = {
  children: ReactNode
}

function Layout({ children }: LayoutProps) {
  return (
    <SnackbarProvider>
      <LayoutWithSnackbar>{children}</LayoutWithSnackbar>
    </SnackbarProvider>
  )
}

function LayoutWithSnackbar({ children }: { children: ReactNode }) {
  const { snackbar, closeSnackbar } = useSnackbarContext()
  return (
    <Box
      sx={{
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'left',
        textAlign: 'left',
      }}
    >
      {children}
      <Snackbar
        openState={[snackbar.open, closeSnackbar]}
        alertProps={{
          message: snackbar.msg,
          severity: snackbar.severity,
        }}
      />
    </Box>
  )
}

export default Layout
