import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Paper from '@mui/material/Paper'
import { createFileRoute, Link } from '@tanstack/react-router'
import { ThemeToggleButton } from '~/components/ui/ThemeToggleButton'

export const Route = createFileRoute('/_pathlessLayout/')({
  component: Home,
})

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
    >
      <Paper elevation={3} sx={{ p: 5, maxWidth: 800, width: '100%', textAlign: 'center', borderRadius: 4 }}>
        <Typography variant="h4" component="h1" sx={{ mb: 2, fontWeight: 700 }}>
          Welcome to ORBITOS v2!
        </Typography>
        <Typography variant="body1" sx={{ mb: 3 }}>
          ORBITOS v2 is faster, better looking and most importantly - more fancy than its predecessor! Crazy right?
        </Typography>
        <Typography variant="body1" sx={{ mb: 3 }}>
          Easily manage all kinds of devices, monitor data in real time, and streamline your scientific workflow to perform real science, wow!
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 2 }}>
          <Typography variant="body2">Theme:</Typography>
          <ThemeToggleButton />
        </Box>
        <Typography variant="caption" color="text.secondary">
          Need help? {'->'}{' '}
          <a
            href="mailto:lars.eggimann@unibe.ch?subject=ORBITOS-v2"
            style={{ color: 'inherit', textDecoration: 'underline' }}
          >
            Contact Lars!
          </a>
        </Typography>
      </Paper>
    </Box>
  )
}
