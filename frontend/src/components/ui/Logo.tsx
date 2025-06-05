import logoImage from '~/assets/orbitos-v2-logo.png'

function Logo() {
  return (
    <img
      src={logoImage}
      alt="ORBITOS Logo"
      style={{ height: 40, width: 'auto', display: 'block' }}
      draggable={false}
    />
  );
}

export { Logo };