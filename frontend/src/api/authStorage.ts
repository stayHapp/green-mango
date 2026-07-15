/** 三端真实 API 会话的浏览器持久化工具。 */

import type { ClientRole } from '../types'

export interface AccessSession {
  accessToken: string
  tokenType: string
  expiresAt: string
  subjectId: number
  subjectType: ClientRole
}

export interface StoredClientSession<T> {
  user: T
  access: AccessSession
}

export const SESSION_STORAGE_KEYS: Record<ClientRole, string> = {
  admin: 'green-mango-admin-api-session',
  guest: 'green-mango-guest-api-session',
  staff: 'green-mango-staff-api-session',
}

/**
 * 判断访问会话是否仍在有效期内。
 *
 * 入参：access 为服务端签发的访问会话，必填。
 * 返回值：boolean：过期时间合法且晚于当前浏览器时间时返回 true。
 * 异常：当前函数不主动抛出异常；非法日期按已过期处理。
 */
export function isAccessSessionValid(access: AccessSession): boolean {
  const expiresAt = new Date(access.expiresAt).getTime()
  return Number.isFinite(expiresAt) && expiresAt > Date.now()
}

/**
 * 从 localStorage（本地存储）读取指定客户端的有效 API 会话。
 *
 * 入参：role 为 admin、staff 或 guest，必填。
 * 返回值：StoredClientSession<T> | undefined：解析成功且未过期时返回会话，否则返回 undefined。
 * 异常：浏览器存储不可用、JSON 无效或结构不完整时会被捕获并返回 undefined。
 */
export function readClientSession<T>(role: ClientRole): StoredClientSession<T> | undefined {
  try {
    const value = window.localStorage.getItem(SESSION_STORAGE_KEYS[role])
    if (!value) {
      return undefined
    }
    const session = JSON.parse(value) as StoredClientSession<T>
    if (!session.user || !session.access?.accessToken || !isAccessSessionValid(session.access)) {
      window.localStorage.removeItem(SESSION_STORAGE_KEYS[role])
      return undefined
    }
    return session
  } catch {
    return undefined
  }
}

/**
 * 将指定客户端的用户展示数据和 API 会话写入 localStorage。
 *
 * 入参：role 为客户端角色；session 为用户与访问凭证组合，均必填。
 * 返回值：void：只产生浏览器本地存储副作用。
 * 异常：浏览器存储被禁用或空间不足时会被捕获，内存会话仍可继续使用。
 */
export function writeClientSession<T>(role: ClientRole, session: StoredClientSession<T>): void {
  try {
    window.localStorage.setItem(SESSION_STORAGE_KEYS[role], JSON.stringify(session))
  } catch {
    // 本地存储失败不应阻断本次已成功的服务端登录。
  }
}

/**
 * 删除指定客户端的本地 API 会话。
 *
 * 入参：role 为待退出的客户端角色，必填。
 * 返回值：void：删除成功或存储不可用时均正常结束。
 * 异常：浏览器存储异常会被捕获，避免影响退出跳转。
 */
export function removeClientSession(role: ClientRole): void {
  try {
    window.localStorage.removeItem(SESSION_STORAGE_KEYS[role])
  } catch {
    // 即使本地存储不可用，也允许 Pinia 内存状态完成清理。
  }
}

/**
 * 读取指定客户端当前可用的 Bearer token。
 *
 * 入参：role 为客户端角色，必填。
 * 返回值：string | undefined：存在未过期会话时返回 token，否则返回 undefined。
 * 异常：读取或解析失败时由 readClientSession 内部处理。
 */
export function readAccessToken(role: ClientRole): string | undefined {
  return readClientSession(role)?.access.accessToken
}
