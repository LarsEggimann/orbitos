import React, { createContext, useContext, useEffect, useState } from 'react';

export type AppConfig = {
  API_BASE_URL: string;
  API_WEBSOCKET_URL: string;
  [key: string]: any;
};

const ConfigContext = createContext<AppConfig | undefined>(undefined);

export const ConfigProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [config, setConfig] = useState<AppConfig | undefined>(undefined);

  useEffect(() => {
    // Determine which config file to load
    // Vite sets import.meta.env.MODE to 'development', 'production', or 'test'
    // 'npm run dev' => 'development', 'npm run preview' => 'production'
    const isDev = import.meta.env.MODE === 'development';
    const configFile = isDev ? '/config-dev.json' : '/config-preview.json';
    console.log('Loading config file:', configFile);
    fetch(configFile)
      .then((res) => res.json())
      .then((data) => setConfig(data));
  }, []);

  if (!config) return null; // or a loading spinner

  return (
    <ConfigContext.Provider value={config}>{children}</ConfigContext.Provider>
  );
};

export function useConfig() {
  const ctx = useContext(ConfigContext);
  if (!ctx) throw new Error('useConfig must be used within a ConfigProvider');
  return ctx;
}
