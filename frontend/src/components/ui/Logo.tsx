import { useThemeMode } from '~/provider/ThemeProvider'

export default function Logo() {
  const { logoSrc } = useThemeMode()
  
  return (
    <img
      src={logoSrc}
      alt='ORBITOS Logo'
      style={{ height: 40, width: 'auto', display: 'block' }}
      draggable={false}
    />
  )
}
