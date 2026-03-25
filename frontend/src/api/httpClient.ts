import axios, { AxiosError } from 'axios'
import { API_BASE_URL } from './config'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export function getApiErrorMessage(error: unknown, fallbackMessage: string): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string; message?: string }>
    const apiMessage = axiosError.response?.data?.detail ?? axiosError.response?.data?.message

    if (apiMessage && apiMessage.trim().length > 0) {
      return apiMessage
    }

    if (axiosError.code === 'ECONNABORTED') {
      return 'Превышено время ожидания ответа сервера'
    }

    if (!axiosError.response) {
      return 'Не удалось подключиться к серверу. Проверьте доступность API.'
    }
  }

  return fallbackMessage
}
