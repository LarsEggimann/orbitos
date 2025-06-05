import { ReactNode } from 'react'
import { AppProvider, DashboardLayout, type Navigation } from '@toolpad/core';

import { Logo } from '~/components/ui/Logo';

type LayoutProps = {
  children: ReactNode
}

function Layout({ children }: LayoutProps) {
  return (
    <AppProvider>
      <DashboardLayout
        branding={{
          title: "ORBITOS v2",
          homeUrl: "/",
          logo: <Logo />,
        }}
      >
        {children}
      </DashboardLayout>
    </AppProvider>
  );
}

export default Layout;