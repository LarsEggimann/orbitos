import { ReactNode } from 'react'
import { AppProvider, DashboardLayout, type Navigation } from '@toolpad/core';
import { MdElectricBolt } from "react-icons/md";
import { FaHome } from "react-icons/fa";

import Logo from '~/components/ui/Logo';
import { Box } from '@mui/material';
import { useRouter } from '@tanstack/react-router';

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
];


type LayoutProps = {
  children: ReactNode
}

function Layout({ children }: LayoutProps) {
  return (
    <AppProvider
      navigation={NAVIGATION}
      
    >
      <DashboardLayout
        branding={{
          title: "ORBITOS v2",
          homeUrl: "/",
          logo: <Logo />,
        }}
        
      >

        <Box
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'left',
            textAlign: 'left',
          }}
        >
          {children}
        </Box>
      </DashboardLayout>
    </AppProvider>
  );
}

export default Layout;