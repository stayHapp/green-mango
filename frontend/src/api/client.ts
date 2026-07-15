/** Axios（HTTP 请求客户端）基础配置和通用错误处理。 */

import axios, { AxiosError, type AxiosRequestConfig } from 'axios'

import type { ClientRole } from '../types'
import { readAccessToken } from './authStorage'

export interface ApiErrorBody {
  detail?: string | Array<{ msg?: string }>
}

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || 'http://127.0.0.1:8000/api'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
})

/**
 * 为指定客户端生成携带 Bearer token 的 Axios 请求配置。
 *
 * 入参：role 为 admin、staff 或 guest；额外配置可选，用于补充查询参数等设置。
 * 返回值：AxiosRequestConfig：带 Authorization 请求头的配置对象。
 * 异常：当前客户端没有有效本地会话时抛出 Error，调用方应跳转登录页。
 * 使用示例：`apiClient.get('/admin/meetings', authorizationConfig('admin'))`。
 */
export function authorizationConfig(role: ClientRole, extra: AxiosRequestConfig = {}): AxiosRequestConfig {
  const token = readAccessToken(role)
  if (!token) {
    throw new Error('登录状态已失效，请重新登录。')
  }
  return {
    ...extra,
    headers: {
      ...extra.headers,
      Authorization: `Bearer ${token}`,
    },
  }
}

/**
 * 将 Axios、FastAPI 和网络异常转换为适合页面展示的中文提示。
 *
 * 入参：error 为任意捕获到的异常；fallback 为无法识别时的默认提示。
 * 返回值：string：优先使用后端 detail，其次区分网络问题，最后返回默认提示。
 * 异常：当前函数不主动抛出异常。
 */
export function getApiErrorMessage(error: unknown, fallback = '请求失败，请稍后重试。'): string {
  if (error instanceof Error && !axios.isAxiosError(error)) {
    return error.message || fallback
  }
  if (!axios.isAxiosError<ApiErrorBody>(error)) {
    return fallback
  }
  const axiosError = error as AxiosError<ApiErrorBody>
  const detail = axiosError.response?.data?.detail
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item.msg).filter(Boolean)
    if (messages.length) {
      return messages.join('；')
    }
  }
  if (!axiosError.response) {
    return '无法连接后端服务，请确认 API 已启动。'
  }
  return fallback
}
