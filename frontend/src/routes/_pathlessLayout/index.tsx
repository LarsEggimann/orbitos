import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Paper from '@mui/material/Paper'
import { createFileRoute } from '@tanstack/react-router'
import { ThemeToggleButton } from '~/components/ui/ThemeToggleButton'
import Logo from '~/components/ui/Logo'
import { keyframes } from '@mui/system'
import Divider from '@mui/material/Divider'

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
        alignItems: 'flex-start', // move landing card up a bit
        justifyContent: 'center',
        py: 6,
      }}
    >
      <Box sx={{ width: '100%', maxWidth: 800 }}>
        <Paper
          elevation={2}
          sx={{
            p: 5,
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

        {/* changelog box */}
        <Paper elevation={2} sx={{ p: 3, mt: 3, borderRadius: 4 }}>
          <Typography variant='h6' sx={{ fontWeight: 600, mb: 1 }}>
            Changelog
          </Typography>
          <Typography variant='body2' color='text.secondary' sx={{ mb: 2 }}>
            Quick notes of what changed since last build.
          </Typography>
          <Divider sx={{ m: 2 }} />
          <ChangelogStatic />
        </Paper>
      </Box>
    </Box>
  )
}

// === simple hard-coded changelog ===
type ChangelogEntry = {
  date: string
  items: string[]
}

const CHANGELOG: ChangelogEntry[] = [
      {
    date: '2025-11-10',
    items: [
      'Add source voltage data to electrometer database as separate table, store source voltage only when it changes, null indicates unknown state (data not yet available in frontend)',
      'Add voltage de-ramp when turning off source voltage to reduce capacitive spikes',
      'Try catch errors during trigger based measurements which prevented the electrometer controller from returning to idle state',
      'Try fix "Lock ... is bound to a different event loop" error in WebSocketManager by using different locking',
      'Try fix "no running event loop" error in run_async_in_background utility function',
    ],
  },
    {
    date: '2025-11-06',
    items: [
      'Fix being able to start multiple voltage sweeps in parallel',
      'Fix electrometer trigger based measurements where the data was showing spikes when using source voltage of the same electrometer (quick toggle of output voltage caused capacitive spikes e.g when connected to the ionization chamber)',
      'Fix date range persisting in electrometer component',
      'Fix settings state reloading when switching devices via sidebar',
      'Allow disconnecting axis of the stages even when they are not idle',
      'New Logo! :)',
    ],
  },
  {
    date: '2025-11-05',
    items: [
      'Download CSV now uses "ch" locale in its default time formatting',
      'Plot on electrometer page now shows dose rate in hover data using the given conversion factor',
      'Conversion factor is now properly persisted in localStorage and accepts exponential notation (e.g., 1e6)',
    ],
  },
  {
    date: '2025-11-04',
    items: [
      'Add "Move to Position" button with inputfield for chopperwheel',
    ],
  },
]

function ChangelogStatic() {
  return (
    <Box>
      {CHANGELOG.map((entry) => (
        <Box key={entry.date} sx={{ mb: 2 }}>
          <Typography variant='subtitle2' color='text.secondary'>
            {entry.date}
          </Typography>
          <Box component='ul' sx={{ m: 0, pl: 3 }}>
            {entry.items.map((it, idx) => (
              <li key={idx}>
                <Typography variant='body2' color='text.secondary'>{it}</Typography>
              </li>
            ))}
          </Box>
          <Divider sx={{ mt: 2 }} />
        </Box>
      ))}
    </Box>
  )
}
