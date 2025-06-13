import type { AxiosError } from 'axios';


export function isAxiosError(obj: any): obj is AxiosError<any> {
    return obj && obj.isAxiosError;
}

export function replaceUnderscores(str: string): string {
    return str.replace(/_/g, ' ');
}



const localTzOffsetSeconds = - new Date().getTimezoneOffset() * 60;
// parse timestamp and convert to localized string with microsecond perecision
export function fromTimestampToLocalizedString(timestampSeconds: number): string {
    // // Example input:  "1749841772.7546272"
    // // Example output: "2025-06-13T21:02:30.244260"

    const shiftedSeconds = timestampSeconds + localTzOffsetSeconds
    const milliseconds = Math.floor(shiftedSeconds * 1000);
    const microseconds = Math.round((shiftedSeconds * 1_000_000) % 1_000_000);

    const date = new Date(milliseconds);
    const isoBase = date.toISOString().slice(0, -5); // "YYYY-MM-DDTHH:mm:ss"

    const microsecondStr = microseconds.toString().padStart(6, '0');

    return `${isoBase}.${microsecondStr}`;
}
