import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Paper from '@mui/material/Paper'
import { createFileRoute } from '@tanstack/react-router'
import { ThemeToggleButton } from '~/components/ui/ThemeToggleButton'
import Logo from '~/components/ui/Logo'
import { keyframes } from '@mui/system'

export const Route = createFileRoute('/_pathlessLayout/')({
  component: Home,
})

const spinAndPulse = keyframes`
  0% {
    transform: rotate(0deg) scale(1);
    filter: drop-shadow(0 0 5px rgba(0, 123, 255, 0.3));
  }
  25% {
    transform: rotate(90deg) scale(1.1);
    filter: drop-shadow(0 0 15px rgba(0, 123, 255, 0.6));
  }
  50% {
    transform: rotate(180deg) scale(1.2);
    filter: drop-shadow(0 0 25px rgba(0, 123, 255, 0.8));
  }
  75% {
    transform: rotate(270deg) scale(1.1);
    filter: drop-shadow(0 0 15px rgba(0, 123, 255, 0.6));
  }
  100% {
    transform: rotate(360deg) scale(1);
    filter: drop-shadow(0 0 5px rgba(0, 123, 255, 0.3));
  }
`

const float = keyframes`
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
`

function Home() {
  return (
    <Box
      sx={{
        bgcolor: 'background.default',
        minHeight: '100vh',
        width: '100vw',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >        <Paper
      elevation={3}
      sx={{
        p: 5,
        maxWidth: 800,
        width: '100%',
        textAlign: 'center',
        borderRadius: 4,
      }}
    >
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            mb: 3,
            animation: `${float} 3s ease-in-out infinite`,
          }}
        >
          <Box
            sx={{
              animation: `${spinAndPulse} 4s linear infinite`,
              '&:hover': {
                animation: `${spinAndPulse} 1s linear infinite`,
              },
              transition: 'all 0.3s ease',
            }}
          >
            <Logo />
          </Box>
        </Box>
        <Typography variant='h4' component='h1' sx={{ mb: 2, fontWeight: 700 }}>
          Welcome to ORBITOS v2!
        </Typography>
        <Typography variant='body1' sx={{ mb: 3 }}>
          ORBITOS v2 is faster, better looking and most importantly - more fancy
          than its predecessor! Crazy right?
        </Typography>
        <Typography variant='body1' sx={{ mb: 3 }}>
          Easily manage all kinds of devices, monitor data in real time, and
          streamline your scientific workflow to perform real science, wow!
        </Typography>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 1,
            mb: 2,
          }}
        >
          <Typography variant='body2'>Theme:</Typography>
          <ThemeToggleButton />
        </Box>
        <Typography variant='caption' color='text.secondary'>
          Need help? {'->'}{' '}
          <a
            href='mailto:lars.eggimann@unibe.ch?subject=ORBITOS-v2'
            style={{ color: 'inherit', textDecoration: 'underline' }}
          >
            Contact Lars!
          </a>
        </Typography>
      </Paper>
    </Box>
  )
}
