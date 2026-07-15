/** 三端真实 API 会话状态与持久化。 */

import { defineStore } from 'pinia'

import {
  readClientSession,
  removeClientSession,
  type AccessSession,
  type StoredClientSession,
  writeClientSession,
} from '../api/authStorage'
import type { AdminUser, ClientRole, Guest, StaffUser } from '../types'

/**
 * 创建 Pinia 初始会话状态，过滤已过期或旧版 Mock 存储。
 *
 * 入参：无。
 * 返回值：包含三端用户和访问会话的状态对象。
 * 异常：浏览器存储读取异常由 readClientSession 内部捕获。
 */
function createInitialState() {
  const adminSession = readClientSession<AdminUser>('admin')
  const guestSession = readClientSession<Guest>('guest')
  const staffSession = readClientSession<StaffUser>('staff')
  return {
    admin: adminSession?.user,
    adminAccess: adminSession?.access,
    guest: guestSession?.user,
    guestAccess: guestSession?.access,
    staff: staffSession?.user,
    staffAccess: staffSession?.access,
  }
}

export const useSessionStore = defineStore('session', {
  state: createInitialState,
  actions: {
    /**
     * 保存管理员展示数据和真实访问会话。
     *
     * 入参：admin 为页面兼容的管理员数据；access 为后端签发会话，均必填。
     * 返回值：void：同步更新 Pinia 和 localStorage。
     * 异常：本地存储写入异常由工具函数捕获。
     */
    setAdmin(admin: AdminUser, access: AccessSession): void {
      this.admin = admin
      this.adminAccess = access
      writeClientSession<AdminUser>('admin', { user: admin, access })
    },
    /**
     * 保存嘉宾展示数据和真实访问会话。
     *
     * 入参：guest 为完整嘉宾资料；access 为后端签发会话，均必填。
     * 返回值：void：同步更新 Pinia 和 localStorage。
     * 异常：本地存储写入异常由工具函数捕获。
     */
    setGuest(guest: Guest, access: AccessSession): void {
      this.guest = guest
      this.guestAccess = access
      writeClientSession<Guest>('guest', { user: guest, access })
    },
    /**
     * 保存工作人员展示数据和真实访问会话。
     *
     * 入参：staff 为页面兼容的工作人员数据；access 为后端签发会话，均必填。
     * 返回值：void：同步更新 Pinia 和 localStorage。
     * 异常：本地存储写入异常由工具函数捕获。
     */
    setStaff(staff: StaffUser, access: AccessSession): void {
      this.staff = staff
      this.staffAccess = access
      writeClientSession<StaffUser>('staff', { user: staff, access })
    },
    /**
     * 清除管理员端本地会话。
     *
     * 入参：无。
     * 返回值：void：清空内存和本地存储。
     * 异常：存储异常由工具函数捕获。
     */
    clearAdmin(): void {
      this.admin = undefined
      this.adminAccess = undefined
      removeClientSession('admin')
    },
    /**
     * 清除嘉宾端本地会话。
     *
     * 入参：无。
     * 返回值：void：清空内存和本地存储。
     * 异常：存储异常由工具函数捕获。
     */
    clearGuest(): void {
      this.guest = undefined
      this.guestAccess = undefined
      removeClientSession('guest')
    },
    /**
     * 清除工作人员端本地会话。
     *
     * 入参：无。
     * 返回值：void：清空内存和本地存储。
     * 异常：存储异常由工具函数捕获。
     */
    clearStaff(): void {
      this.staff = undefined
      this.staffAccess = undefined
      removeClientSession('staff')
    },
    /**
     * 清除指定客户端会话，用于统一处理退出和过期状态。
     *
     * 入参：role 为 admin、staff 或 guest，必填。
     * 返回值：void：调用对应客户端清理动作。
     * 异常：当前函数不主动抛出异常。
     */
    clearRole(role: ClientRole): void {
      if (role === 'admin') {
        this.clearAdmin()
      } else if (role === 'staff') {
        this.clearStaff()
      } else {
        this.clearGuest()
      }
    },
  },
})

export type { AccessSession, StoredClientSession }
