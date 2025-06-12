import * as React from 'react';
import { DateTimePicker, DateTimePickerProps } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';


export type DateRangeSelectProps = {
    startState: [Date | null, React.Dispatch<React.SetStateAction<Date | null>>];
    endState: [Date | null, React.Dispatch<React.SetStateAction<Date | null>>];
} & DateTimePickerProps;

const DateRangeSelect: React.FC<DateRangeSelectProps> = ({
    startState,
    endState,
    ...rest
}) => {

    const [startDate, setStartDate] = startState;
    const [endDate, setEndDate] = endState;


    return (
        <LocalizationProvider dateAdapter={AdapterDayjs}>
            <DateTimePicker
                label="Start Date Time"
                ampm={false}
                value={startDate ? dayjs(startDate) : null}
                onChange={(newValue) => {
                    setStartDate(newValue ? newValue.toDate() : null);
                }}
                timezone='system'
                {...rest}
            />
                
            <DateTimePicker
                label="End Date Time"
                ampm={false}
                value={endDate ? dayjs(endDate) : null}
                onChange={(newValue) => {
                    setEndDate(newValue ? newValue.toDate() : null);
                }}
                {...rest}
            />

        </LocalizationProvider>

    );
};

export default DateRangeSelect;
