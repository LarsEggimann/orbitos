import logoImage from '~/assets/orbitos-v2-logo.png'

export default function Logo() {
  return (
    <img
      src={logoImage}
      alt='ORBITOS Logo'
      style={{ height: 40, width: 'auto', display: 'block' }}
      draggable={false}
    />
  )
}
