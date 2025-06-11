import * as React from 'react';
import Button, { ButtonProps } from '@mui/material/Button';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import type { AxiosResponse, AxiosError } from 'axios';

export type ReusableButtonProps = {
    onClick?: () => Promise<AxiosResponse<any> | AxiosError<any> | void>;
} & ButtonProps;

const ReusableButton: React.FC<ReusableButtonProps> = ({
    onClick,
    variant = 'outlined',
    color = 'primary',
    sx,
    children,
    ...rest
}) => {
    const [loading, setLoading] = React.useState(false);
    const [toastMsg, setToastMsg] = React.useState<string | null>(null);
    const [toastSeverity, setToastSeverity] = React.useState<'success' | 'error'>('success');
    const [open, setOpen] = React.useState(false);

    function isAxiosError(obj: any): obj is AxiosError<any> {
        return obj && obj.isAxiosError;
    }

    const handleClick = async () => {
        if (!onClick) return;
        setLoading(true);
        setToastMsg(null);
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
            <Button
                variant={variant}
                color={color}
                onClick={handleClick}
                loading={loading}
                loadingPosition="start"
                sx={{
                    textTransform: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    textAlign: 'center',
                    ...sx,
                }}
                {...rest}
            >
                {children}
            </Button>
            <Snackbar open={open} autoHideDuration={4000} onClose={() => setOpen(false)} anchorOrigin={{ vertical: 'top', horizontal: 'center' }}>
                <Alert onClose={() => setOpen(false)} severity={toastSeverity} sx={{ width: '100%' }}>
                    {toastMsg}
                </Alert>
            </Snackbar>
        </>
    );
};

export default ReusableButton;
