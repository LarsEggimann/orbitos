import React, { useState, useEffect } from 'react'
import { Box, Typography, CircularProgress } from '@mui/material'
import PrestyledButton from './PrestyledButton'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'

interface ServerStatusIndicatorProps {
  url: string
  checkInterval?: number
}

const ServerStatusIndicator: React.FC<ServerStatusIndicatorProps> = ({
  url,
  checkInterval = 10000, // 10 seconds
}) => {
  const [isOnline, setIsOnline] = useState<boolean | null>(null)
  const [isChecking, setIsChecking] = useState(false)
  const [isPageVisible, setIsPageVisible] = useState(!document.hidden)

  const checkServerStatus = async () => {
    setIsChecking(true)
    try {
      await fetch(url, { 
        method: 'HEAD',
        mode: 'no-cors' // This helps with CORS issues
      })
      setIsOnline(true)
    } catch {
      setIsOnline(false)
    } finally {
      setIsChecking(false)
    }
  }

  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsPageVisible(!document.hidden)
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])

  useEffect(() => {
    if (!isPageVisible) return // Don't check when page is not visible

    // Initial check when page becomes visible
    checkServerStatus()

    // Set up interval for periodic checks only when page is visible
    const interval = setInterval(() => {
      if (!document.hidden) { // Double-check visibility before each request
        checkServerStatus()
      }
    }, checkInterval)

    return () => clearInterval(interval)
  }, [url, checkInterval, isPageVisible])

  const getStatusColor = () => {
    if (isOnline === null || isChecking) return 'orange'
    return isOnline ? 'green' : 'red'
  }

  const getStatusText = () => {
    if (isChecking) return 'Checking...'
    if (isOnline === null) return 'Unknown'
    return isOnline ? 'Online' : 'Offline'
  }

  const handleOpenDocs = () => {
    window.open(url, '_blank', 'noopener,noreferrer')
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box
          sx={{
            width: 12,
            height: 12,
            borderRadius: '50%',
            backgroundColor: getStatusColor(),
            position: 'relative',
          }}
        >
          {isChecking && (
            <CircularProgress
              size={16}
              sx={{
                position: 'absolute',
                top: -2,
                left: -2,
                color: 'primary.main',
              }}
            />
          )}
        </Box>
        <Typography variant="body2" sx={{ minWidth: 80 }}>
          {getStatusText()}
        </Typography>
      </Box>
      
      <PrestyledButton
        onClick={handleOpenDocs}
        startIcon={<OpenInNewIcon />}
        size="small"
        disabled={!isOnline}
        tooltip={isOnline ? 'Open Raspi Server Documentation' : 'Server is offline'}
      >
        Open Docs
      </PrestyledButton>
    </Box>
  )
}

export default ServerStatusIndicator
