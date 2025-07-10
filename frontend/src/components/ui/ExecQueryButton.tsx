import * as React from 'react'
import type { AxiosResponse, AxiosError } from 'axios'

import PrestyledButton from './PrestyledButton'
import { useExecQueryHelper } from '../../utils/ExecQueryHelper'

export type ReusableButtonProps = {
  onClick?: () => Promise<AxiosResponse<any> | AxiosError<any> | void>
} & React.ComponentProps<typeof PrestyledButton>

const ExecQueryButton: React.FC<ReusableButtonProps> = ({
  onClick,
  children,
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
      {...rest}
    >
      {children}
    </PrestyledButton>
  )
}

export default ExecQueryButton
