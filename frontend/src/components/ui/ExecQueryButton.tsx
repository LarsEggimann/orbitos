import * as React from 'react'
import type { AxiosResponse, AxiosError } from 'axios'

import PrestyledButton from './PrestyledButton'
import { isAxiosError } from '~/utils/helpers'
import { useSnackbarContext } from '~/provider/SnackbarProvider'

export type ReusableButtonProps = {
  onClick?: () => Promise<AxiosResponse<any> | AxiosError<any> | void>
} & React.ComponentProps<typeof PrestyledButton>

const ExecQueryButton: React.FC<ReusableButtonProps> = ({
  onClick,
  children,
  ...rest
}) => {
  const [loading, setLoading] = React.useState(false)
  const { openSnackbar } = useSnackbarContext()

  const handleClick = async () => {
    if (!onClick) return
    setLoading(true)
    try {
      const result = await onClick()
      if (isAxiosError(result)) {
        const msg =
          result.response?.data?.message ||
          result.message ||
          'An error occurred'
        const additionalInfo = result.response?.data?.detail || ''
        openSnackbar(
          msg + (additionalInfo ? `: ${additionalInfo}` : ''),
          'error',
        )
      } else if (
        result &&
        typeof result === 'object' &&
        'data' in result &&
        result.data &&
        typeof result.data === 'object' &&
        'message' in result.data
      ) {
        const msg = (result.data as any).message
        if (typeof msg === 'string') {
          openSnackbar(msg, 'success')
        }
      }
    } catch (err: any) {
      const msg =
        err?.response?.data?.message || err?.message || 'An error occurred'
      openSnackbar(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <PrestyledButton
      onClick={handleClick}
      disabled={loading || rest.disabled}
      {...rest}
    >
      {children}
    </PrestyledButton>
  )
}

export default ExecQueryButton
