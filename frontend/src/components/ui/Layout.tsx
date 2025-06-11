import { ReactNode } from 'react'
import { AppProvider, DashboardLayout, type Navigation } from '@toolpad/core';
import { MdElectricBolt } from "react-icons/md";
import { FaHome } from "react-icons/fa";

import Logo from '~/components/ui/Logo';
import { Box } from '@mui/material';

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
    // <AppProvider
    //   navigation={NAVIGATION}
      
    // >
    //   <DashboardLayout
    //     branding={{
    //       title: "ORBITOS v2",
    //       homeUrl: "/",
    //       logo: <Logo />,
    //     }}
        
    //   >
    //     </DashboardLayout>
    //   </AppProvider>

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
        </Box>
  );
}

export default Layout;