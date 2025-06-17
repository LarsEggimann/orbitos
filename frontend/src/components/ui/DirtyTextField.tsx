import React, {
  useState,
  forwardRef,
  useImperativeHandle,
  useRef,
  useEffect
} from 'react';
import TextField, { TextFieldProps } from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Select, { SelectChangeEvent } from '@mui/material/Select';

export type DirtyTextFieldProps = {
  /**
   * Called when Enter is pressed or apply is called, returning Promise<boolean> true if the value was applied successfully, false otherwise.
   */
  onApply?: (value: string) => Promise<boolean>;

  /**
   * Set to true to show the field as ON/OFF dropdown instead of a text field.
   */
  onOff?: boolean;
} & TextFieldProps;

export type DirtyTextFieldHandle = {
  tryApply: () => void;
};

const DirtyTextField = forwardRef<DirtyTextFieldHandle, DirtyTextFieldProps>(
  ({ onApply, onOff = false, ...rest }, ref) => {
    const [dirty, setDirty] = useState(false);
    const [value, setValue] = useState(rest.value);

    // keep internal state in sync if `rest.value` changes
    useEffect(() => {
      setValue(rest.value);
    }, [rest.value]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setDirty(true);
      setValue(e.target.value);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        tryApply();
      }
    };

    const tryApply = async () => {
      console.log('Trying to apply value:', value, 'dirty:', dirty);
      if (dirty) {
        doTryApply(String(value));
      }
    };

    const doTryApply = async (newValue: string) => {
      if (onApply) {
        try {
          const result = await onApply(String(newValue));
          if (result === true) {
            setDirty(false);
          }
        } catch {
          // do not clear dirty on error
        }
      }
    }

    useImperativeHandle(ref, () => ({
      tryApply,
    }));

    return (
      onOff ? (
        <Select
          {...rest} // TODO fix this mess!!!
          value={value}
          onChange={e => {
            console.log('Select changed:', e.target.value);
            setDirty(true);
            setValue(e.target.value);
            doTryApply(e.target.value as string);


          }}
          color={dirty ? 'warning' : rest.color || 'primary'}
        >
          <MenuItem value="ON">ON</MenuItem>
          <MenuItem value="OFF">OFF</MenuItem>
        </Select>
      ) : (
        <TextField
          {...rest}
          value={value}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          color={dirty ? 'warning' : rest.color || 'primary'}
          type={typeof value === 'number' ? 'number' : 'text'}
          focused={dirty || rest.focused}
        />
      )
    );
  }
);

export default DirtyTextField;
