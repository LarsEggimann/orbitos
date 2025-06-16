import React, { useEffect, useState } from 'react'
import CircularProgress from '@mui/material/CircularProgress'
import Box from '@mui/material/Box'
import Skeleton from '@mui/material/Skeleton'
import type { UseQueryResult } from '@tanstack/react-query'

interface LoadingOverlayProps {
  loading?: boolean
  query?: UseQueryResult<any, Error>
  height?: string | number
  slowMessage?: React.ReactNode
  slowTimeoutMs?: number
}

/**
 * Created with ChatJypidyyy!
 * 
 * Displays a Material UI spinner and skeleton overlay when loading is true or query is loading/fetching.
 * Shows a message if loading takes longer than slowTimeoutMs (default 3000ms).
 *
 * Usage:
 * <LoadingOverlay loading={isLoading} height={400} />
 * <LoadingOverlay query={query} height={400} />
 */
const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  loading,
  query,
  height = 400,
  slowMessage = (
    <Box mt={2} sx={{ color: 'text.secondary', textAlign: 'center', maxWidth: 500 }}>
      loading large amount of data, this may take a while ...<br />consider reducing timeframe!
    </Box>
  ),
  slowTimeoutMs = 3000,
}) => {
  const isLoading = loading ?? (query?.isLoading || query?.isFetching)
  const [showSlowMsg, setShowSlowMsg] = useState(false)

  useEffect(() => {
    let timer: NodeJS.Timeout | undefined
    if (isLoading) {
      setShowSlowMsg(false)
      timer = setTimeout(() => setShowSlowMsg(true), slowTimeoutMs)
    } else {
      setShowSlowMsg(false)
    }
    return () => { if (timer) clearTimeout(timer) }
  }, [isLoading, slowTimeoutMs])

  if (!isLoading) return null

  return (
    <>
      <Skeleton variant="rectangular" width="100%" height={height} sx={{ position: 'absolute', top: 0, left: 0, zIndex: 1, borderRadius: 2 }} />
      <Box sx={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        zIndex: 2,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <CircularProgress color="primary" />
        {showSlowMsg && slowMessage}
      </Box>
    </>
  )
}

export default LoadingOverlay
