import * as React from 'react'
import type { AxiosResponse, AxiosError } from 'axios'

import PrestyledButton from './PrestyledButton'
import { useExecQueryHelper } from '../../utils/ExecQueryHelper'

export type ReusableButtonProps = {
  onClick?: () => Promise<AxiosResponse<any> | AxiosError<any> | void>
  tooltip?: string
} & React.ComponentProps<typeof PrestyledButton>

const ExecQueryButton: React.FC<ReusableButtonProps> = ({
  onClick,
  children,
  tooltip,
  ...rest
}) => {
  const [loading, setLoading] = React.useState(false)

  const { executeQuery } = useExecQueryHelper()

  const handleClick = async () => {
    if (!onClick) return
    setLoading(true)
    try {
      await executeQuery(onClick)
    } finally {
      setLoading(false)
    }
  }

  return (
    <PrestyledButton
      onClick={handleClick}
      disabled={loading || rest.disabled}
      tooltip={tooltip}
      {...rest}
    >
      {children}
    </PrestyledButton>
  )
}

export default ExecQueryButton
