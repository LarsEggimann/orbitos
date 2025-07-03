import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import {
  ThemeProvider as MuiThemeProvider,
  createTheme,
  CssBaseline,
} from '@mui/material'

export type ThemeMode = 'light' | 'dark' | 'system'

interface ThemeContextType {
  mode: ThemeMode
  setMode: (mode: ThemeMode) => void
  resolvedMode: 'light' | 'dark'
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export const ThemeProvider = ({ children }: { children: React.ReactNode }) => {
  const [mode, setMode] = useState<ThemeMode>(() => {
    if (typeof window === 'undefined') return 'system'
    return (localStorage.getItem('mui-theme-mode') as ThemeMode) || 'system'
  })
  const [resolvedMode, setResolvedMode] = useState<'light' | 'dark'>(() => {
    if (typeof window === 'undefined') return 'light'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light'
  })

  // Listen to system theme changes
  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const update = () => setResolvedMode(media.matches ? 'dark' : 'light')
    media.addEventListener('change', update)
    update()
    return () => media.removeEventListener('change', update)
  }, [])

  // Persist user choice
  useEffect(() => {
    if (mode !== 'system') {
      localStorage.setItem('mui-theme-mode', mode)
    } else {
      localStorage.removeItem('mui-theme-mode')
    }
  }, [mode])

  const appliedMode = mode === 'system' ? resolvedMode : mode

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: appliedMode,
        },
      }),
    [appliedMode],
  )

  return (
    <ThemeContext.Provider value={{ mode, setMode, resolvedMode }}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  )
}

export const useThemeMode = () => {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useThemeMode must be used within ThemeProvider')
  return ctx
}
