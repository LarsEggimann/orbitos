import * as React from 'react';
import Button, { ButtonProps } from '@mui/material/Button';

export type ReusableButtonProps = {
    onClick?: React.MouseEventHandler<HTMLButtonElement>;
} & ButtonProps;

const ReusableButton: React.FC<ReusableButtonProps> = ({
    onClick,
    variant = 'text',
    color = 'primary',
    sx,
    children,
    ...rest
}) => {
    return (
        <Button
            variant={variant}
            color={color}
            onClick={onClick}
            sx={{
                textTransform: 'none', // prevent all caps
                display: 'flex',
                alignItems: 'center', // vertical centering
                ...sx,
            }}
            {...rest}
        >
            {children}
        </Button>
    );
};

export default ReusableButton;
