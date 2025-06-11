import type { AxiosResponse, AxiosError } from 'axios';


export function isAxiosError(obj: any): obj is AxiosError<any> {
    return obj && obj.isAxiosError;
}