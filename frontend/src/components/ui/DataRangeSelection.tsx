import * as React from 'react'
import dayjs from 'dayjs'
import 'dayjs/locale/de'
import {
  DateTimePicker,
  type DateTimePickerProps,
} from '@mui/x-date-pickers/DateTimePicker'
import FastForwardIcon from '@mui/icons-material/FastForward';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import UpdateIcon from '@mui/icons-material/Update';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import Stack from '@mui/material/Stack'

import PrestyledButton from './PrestyledButton'

export type DateRangeSelectProps = {
  startState: [Date | null, React.Dispatch<React.SetStateAction<Date | null>>]
  endState: [Date | null, React.Dispatch<React.SetStateAction<Date | null>>]
} & DateTimePickerProps

const DateRangeSelect: React.FC<DateRangeSelectProps> = ({
  startState,
  endState,
  ...rest
}) => {
  const [startDate, setStartDate] = startState
  const [endDate, setEndDate] = endState

  React.useEffect(() => {
    dayjs.locale('de')
  }, [])

  const setRangeToToday = () => {
    const today = new Date()
    setStartDate(
      new Date(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0, 0),
    )
    setEndDate(null)
  }

  const lastNMinutes = (n: number) => {
    const now = new Date()
    const start = new Date(now.getTime() - n * 60 * 1000)
    setStartDate(start)
    setEndDate(null) // Reset end date to null
  }

  const startMinusNMinutes = (n: number) => {
    if (!startDate) {
      return
    }
    const start = new Date(startDate.getTime() - n * 60 * 1000)
    setStartDate(start)
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale='de'>
      <Stack
        direction='row'
        sx={{
          alignItems: 'center',
          gap: 1,
          justifyContent: 'space-between',
          flexWrap: 'wrap',
        }}
      >
        <Stack
          direction='row'
          sx={{
            alignItems: 'center',
            gap: 1,
            justifyContent: 'flex-end',
            flexWrap: 'wrap',
          }}
        >
          <DateTimePicker
            label='Start Date Time'
            ampm={false}
            value={startDate ? dayjs(startDate) : null}
            onChange={(newValue: dayjs.Dayjs | null) => {
              // check if the time difference between newValue and endDate is more than 24 hours, or if endDate is null, or if start and end are the same
              if (
                newValue &&
                ((endDate &&
                  Math.abs(endDate.getTime() - newValue.toDate().getTime()) >=
                  24 * 60 * 60 * 1000) ||
                  !endDate ||
                  (endDate &&
                    endDate.getTime() === newValue.toDate().getTime()))
              ) {
                // if so, set endDate to 24 hours after newValue
                const newEndDate: Date = new Date(
                  newValue.toDate().getTime() + 24 * 60 * 60 * 1000,
                )
                setEndDate(newEndDate)
              }
              setStartDate(newValue ? newValue.toDate() : null)
            }}
            views={['year', 'month', 'day', 'hours', 'minutes', 'seconds']}
            {...rest}
          />

          <PrestyledButton
            tooltip='Reset to current time'
            onClick={() => {
              lastNMinutes(0)
            }}
          >
            <UpdateIcon />
          </PrestyledButton>

          <PrestyledButton
            tooltip='Go back 60 minutes'
            onClick={() => {
              startMinusNMinutes(60)
            }}
          >
            <FastForwardIcon
              sx={{ transform: 'rotate(180deg)' }}
            />
          </PrestyledButton>
          <PrestyledButton
            tooltip='Go back 5 minutes'
            onClick={() => {
              startMinusNMinutes(5)
            }}
          >
            <PlayArrowIcon
              sx={{ transform: 'rotate(180deg)' }}
            />
          </PrestyledButton>
        
        </Stack>

        <Stack
          direction='row'
          sx={{
            alignItems: 'center',
            gap: 1,
            justifyContent: 'flex-end',
            flexWrap: 'wrap',
          }}
        >
          <DateTimePicker
            label='End Date Time'
            ampm={false}
            value={endDate ? dayjs(endDate) : null}
            onChange={(newValue) => {
              setEndDate(newValue ? newValue.toDate() : null)
            }}
            views={['year', 'month', 'day', 'hours', 'minutes', 'seconds']}
            {...rest}
          />

          <PrestyledButton
            tooltip='Reset end date'
            onClick={() => {
              setEndDate(null)
            }}
          >
            <UpdateIcon />
          </PrestyledButton>
        </Stack>
      </Stack>
    </LocalizationProvider>
  )
}

export default DateRangeSelect
