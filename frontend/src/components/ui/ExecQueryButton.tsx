import * as React from 'react';
import type { AxiosResponse, AxiosError } from 'axios';
import Snackbar from './Snackbar';
import { isAxiosError } from '~/utils/helpers';
import PrestyledButton from './PrestyledButton';

export type ReusableButtonProps = {
    onClick?: () => Promise<AxiosResponse<any> | AxiosError<any> | void>;
} & React.ComponentProps<typeof PrestyledButton>;

const ExecQueryButton: React.FC<ReusableButtonProps> = ({
    onClick,
    children,
    ...rest
}) => {
    const [loading, setLoading] = React.useState(false);
    const [toastMsg, setToastMsg] = React.useState<string | undefined>(undefined);
    const [toastSeverity, setToastSeverity] = React.useState<'success' | 'error'>('success');
    const [open, setOpen] = React.useState(false);

    const handleClick = async () => {
        if (!onClick) return;
        setLoading(true);
        setToastMsg(undefined);
        try {
            const result = await onClick();
            if (isAxiosError(result)) {
                // Error response from axios
                const msg = result.response?.data?.message || result.message || 'An error occurred';
                const additionalInfo = result.response?.data?.detail || '';
                setToastMsg(msg + (additionalInfo ? `: ${additionalInfo}` : ''));
                setToastSeverity('error');
                setOpen(true);
            } else if (result && typeof result === 'object' && 'data' in result && result.data && typeof result.data === 'object' && 'message' in result.data) {
                // Success response
                const msg = (result.data as any).message;
                if (typeof msg === 'string') {
                    setToastMsg(msg);
                    setToastSeverity('success');
                    setOpen(true);
                }
            }
        } catch (err: any) {
            // Network or unexpected error
            const msg = err?.response?.data?.message || err?.message || 'An error occurred';
            setToastMsg(msg);
            setToastSeverity('error');
            setOpen(true);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <PrestyledButton
                onClick={handleClick}
                disabled={loading || rest.disabled}
                {...rest}
            >
                {children}
            </PrestyledButton>
            <Snackbar
                openState={[open, setOpen]}
                alertProps={{
                    message: toastMsg,
                    severity: toastSeverity,
                }}
            />
        </>
    );
};

export default ExecQueryButton;
