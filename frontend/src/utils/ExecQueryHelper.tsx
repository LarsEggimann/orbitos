import { useSnackbarContext } from '~/provider/SnackbarProvider'
import type { AxiosResponse, AxiosError } from 'axios'
import { isAxiosError } from '~/utils/helpers'

export type ExecQueryFunction = () => Promise<AxiosResponse<any> | AxiosError<any> | void>

const handleError = (error: any, onError?: (message: string) => void) => {
  const msg = error?.response?.data?.message || error?.message || 'An error occurred'
  
  if (onError) {
    onError(msg)
  } else {
    throw error
  }
}

const handleAxiosError = (result: AxiosError, onError?: (message: string) => void) => {
  const msg = (result.response?.data as any)?.message || result.message || 'An error occurred'
  const additionalInfo = (result.response?.data as any)?.detail || ''
  const errorMessage = msg + (additionalInfo ? `: ${additionalInfo}` : '')
  
  if (onError) {
    onError(errorMessage)
  } else {
    throw new Error(errorMessage)
  }
}

const handleSuccess = (result: any, onSuccess?: (message: string) => void) => {
  if (
    result &&
    typeof result === 'object' &&
    'data' in result &&
    result.data &&
    typeof result.data === 'object' &&
    'message' in result.data
  ) {
    const msg = result.data.message
    if (typeof msg === 'string' && onSuccess) {
      onSuccess(msg)
    }
  }
}

export const useExecQueryHelper = () => {

  const { openSnackbar } = useSnackbarContext()

  const executeQuery = async (queryFn: ExecQueryFunction) => {
    try {
      const result = await queryFn()
      
      if (isAxiosError(result)) {
        handleAxiosError(result, (message) => openSnackbar(message, 'error'))
      } else {
        handleSuccess(result,  (message) => openSnackbar(message, 'success'))
      }
      
      return result
    } catch (err: any) {
      handleError(err,  (message) => openSnackbar(message, 'error'))
    }
  }

  return { executeQuery }
}
