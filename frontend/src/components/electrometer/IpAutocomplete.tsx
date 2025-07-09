import * as React from 'react'
import Autocomplete, { createFilterOptions } from '@mui/material/Autocomplete'
import TextField from '@mui/material/TextField'

const filter = createFilterOptions<IpOptionType>()

export interface IpOptionType {
  inputValue?: string
  label: string
}

interface IpAutocompleteProps {
  value: string
  onChange: (ip: string) => void
  options: IpOptionType[]
  label?: string
  sx?: any
}

export default function IpAutocomplete({
  value,
  onChange,
  options,
  label = 'Electrometer IP',
  sx,
}: IpAutocompleteProps) {
  const [internalValue, setInternalValue] = React.useState<IpOptionType | null>(
    value ? { label: value } : null,
  )

  React.useEffect(() => {
    setInternalValue(value ? { label: value } : null)
  }, [value])

  return (
    <Autocomplete
      value={internalValue}
      size='small'
      onChange={(_, newValue) => {
        if (typeof newValue === 'string') {
          setInternalValue({ label: newValue })
          onChange(newValue)
        } else if (newValue && newValue.inputValue) {
          setInternalValue({ label: newValue.inputValue })
          onChange(newValue.inputValue)
        } else {
          setInternalValue(newValue)
          onChange(newValue?.label || '')
        }
      }}
      filterOptions={(opts, params) => {
        const filtered = filter(opts, params)
        const { inputValue } = params
        const isExisting = opts.some((opt) => inputValue === opt.label)
        if (inputValue !== '' && !isExisting) {
          filtered.push({ inputValue, label: inputValue })
        }
        return filtered
      }}
      selectOnFocus
      clearOnBlur
      handleHomeEndKeys
      id='electrometer-ip-autocomplete'
      options={options}
      getOptionLabel={(option) => {
        if (typeof option === 'string') return option
        if (option.inputValue) return option.inputValue
        return option.label
      }}
      renderOption={(props, option) => <li {...props}>{option.label}</li>}
      sx={sx}
      freeSolo
      renderInput={(params) => (
        <TextField {...params} label={label} size='small' />
      )}
    />
  )
}
