import { type ReactNode, useState } from 'react'
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  ListItemButton,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import { Link } from '@tanstack/react-router'
import { MdElectricBolt, MdLineAxis } from 'react-icons/md'
import DnsIcon from '@mui/icons-material/Dns';
import OpenInFullIcon from '@mui/icons-material/OpenInFull';
import HomeRepairServiceIcon from '@mui/icons-material/HomeRepairService';
import { FaHome } from 'react-icons/fa'
import { LuShipWheel, LuAxis3D } from 'react-icons/lu'
import { TbArrowMergeBoth } from 'react-icons/tb'

import Logo from '~/components/ui/Logo'
import { SnackbarProvider } from '~/provider/SnackbarProvider'

const drawerWidth = 220

const navLinks = [
  { text: 'Home', icon: <FaHome />, to: '/' },
  { text: 'Electrometer 1', icon: <MdElectricBolt />, to: '/electrometer/1' },
  { text: 'Electrometer 2', icon: <MdElectricBolt />, to: '/electrometer/2' },
  {
    text: 'Electrometer 1 and 2',
    icon: (
      <>
        <MdElectricBolt />
        <MdElectricBolt />
      </>
    ),
    to: '/electrometer/1/and/2',
  },
  { text: 'Chopper Wheel', icon: <LuShipWheel />, to: '/chopperwheel' },
  { text: 'Stages', icon: <LuAxis3D />, to: '/stages' },
  { text: 'Combo Control', icon: <TbArrowMergeBoth />, to: '/combo-control' },
  { text: 'Combo Data View', icon: <MdLineAxis />, to: '/combo-data-view' },
  { text: 'PANDORA Wheels Control', icon: <HomeRepairServiceIcon />, to: '/pandora/wheels' },
  { text: 'PANDORA Linear Actuator', icon: <OpenInFullIcon />, to: '/pandora/linear-actuator' },
  { text: 'PANDORA Server Manage', icon: <DnsIcon />, to: '/pandora/manage' },
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
  const [drawerOpen, setDrawerOpen] = useState(false)

  const handleDrawerToggle = () => {
    setDrawerOpen((open) => !open)
  }

  return (
    <Box sx={{ display: 'flex' }}>
      {/* Side Drawer */}
      <Drawer
        variant='temporary'
        anchor='left'
        open={drawerOpen}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
        }}
      >
        <Toolbar />
        <List>
          {navLinks.map((link) => (
            <ListItem key={link.text} disablePadding sx={{ px: 1 }}>
              <ListItemButton
                component={Link}
                to={link.to}
                onClick={handleDrawerToggle}
                sx={{
                  '&:hover': {
                    backgroundColor: 'action.hover',
                  },
                  'py': 1.5,
                  'px': 2,
                  'borderRadius': 5,
                }}
              >
                <ListItemIcon>{link.icon}</ListItemIcon>
                <ListItemText primary={link.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Drawer>
      <Box sx={{ flexGrow: 1 }}>
        {/* Top Bar */}
        <AppBar
          position='fixed'
          elevation={0}
          color='default'
          sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
        >
          <Toolbar>
            <IconButton
              color='inherit'
              aria-label='open drawer'
              edge='start'
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            <Box
              component={Link}
              to="/"
              sx={{
              display: 'flex',
              alignItems: 'center',
              mr: 2,
              textDecoration: 'none',
              color: 'inherit',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
              <Logo />
              </Box>
              <Typography variant="h6" noWrap component="div">
              ORBITOS v2
              </Typography>
            </Box>
          </Toolbar>
        </AppBar>
        {/* Main Content */}
        <Toolbar />
        <Box
          sx={{
            p: 1,
            m: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'left',
            textAlign: 'left',
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  )
}

export default Layout
