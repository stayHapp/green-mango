/**
 * 三端原型的会话状态。
 *
 * 当前只保存 mock 登录结果，不代表最终鉴权方案。
 */
import { defineStore } from 'pinia'

import type { AdminUser, Guest, StaffUser } from '../types'

const STORAGE_KEYS = {
  admin: 'green-mango-admin-session',
  guest: 'green-mango-guest-session',
  staff: 'green-mango-staff-session',
}

/**
 * 从 localStorage（本地存储）读取指定会话对象。
 *
 * 入参：
 *   key：localStorage 存储键，必填，取值应来自 STORAGE_KEYS。
 *
 * 返回值：
 *   T | undefined：解析成功时返回对应会话对象；不存在或解析失败时返回 undefined。
 *
 * 异常：
 *   JSON 解析失败或浏览器存储不可用时会被捕获，并返回 undefined。
 */
function readStoredSession<T>(key: string): T | undefined {
  try {
    const value = window.localStorage.getItem(key)

    if (!value) {
      return undefined
    }

    return JSON.parse(value) as T
  } catch {
    return undefined
  }
}

/**
 * 将指定会话对象写入 localStorage（本地存储）。
 *
 * 入参：
 *   key：localStorage 存储键，必填，取值应来自 STORAGE_KEYS。
 *   value：需要保存的会话对象，必填。
 *
 * 返回值：
 *   void：只产生浏览器本地存储副作用。
 *
 * 异常：
 *   浏览器存储不可用或写入失败时会被捕获，避免阻断页面流程。
 */
function writeStoredSession<T>(key: string, value: T): void {
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // 忽略本地存储写入失败，确保 mock 登录流程不被浏览器策略阻断。
  }
}

/**
 * 删除指定的 localStorage（本地存储）会话对象。
 *
 * 入参：key 为 localStorage 存储键，必填，取值应来自 STORAGE_KEYS。
 * 返回值：void：只产生浏览器本地存储删除副作用。
 * 异常：浏览器存储不可用或删除失败时会被捕获，避免阻断退出流程。
 */
function removeStoredSession(key: string): void {
  try {
    window.localStorage.removeItem(key)
  } catch {
    // 忽略本地存储删除失败，确保页面仍可完成退出状态切换。
  }
}

export const useSessionStore = defineStore('session', {
  state: () => ({
    admin: readStoredSession<AdminUser>(STORAGE_KEYS.admin),
    guest: readStoredSession<Guest>(STORAGE_KEYS.guest),
    staff: readStoredSession<StaffUser>(STORAGE_KEYS.staff),
  }),
  actions: {
    /**
     * 保存管理员端 mock 登录结果。
     *
     * 入参：
     *   admin：登录成功的管理员对象，必填。
     *
     * 返回值：
     *   void：只更新前端会话状态。
     *
     * 异常：
     *   当前函数不主动抛出异常。
     */
    setAdmin(admin: AdminUser) {
      this.admin = admin
      writeStoredSession(STORAGE_KEYS.admin, admin)
    },
    /**
     * 保存嘉宾端 mock 登录结果。
     *
     * 入参：
     *   guest：登录成功的嘉宾对象，必填。
     *
     * 返回值：
     *   void：只更新前端会话状态。
     *
     * 异常：
     *   当前函数不主动抛出异常。
     */
    setGuest(guest: Guest) {
      this.guest = guest
      writeStoredSession(STORAGE_KEYS.guest, guest)
    },
    /**
     * 保存工作人员端 mock 登录结果。
     *
     * 入参：
     *   staff：登录成功的工作人员对象，必填。
     *
     * 返回值：
     *   void：只更新前端会话状态。
     *
     * 异常：
     *   当前函数不主动抛出异常。
     */
    setStaff(staff: StaffUser) {
      this.staff = staff
      writeStoredSession(STORAGE_KEYS.staff, staff)
    },
    /**
     * 清除管理员端 Mock 会话。
     *
     * 入参：无。
     * 返回值：void：清空状态管理库和本地存储中的管理员会话。
     * 异常：本地存储删除失败时会被内部捕获，不影响内存状态清空。
     */
    clearAdmin(): void {
      this.admin = undefined
      removeStoredSession(STORAGE_KEYS.admin)
    },
    /**
     * 清除嘉宾端 Mock 会话。
     *
     * 入参：无。
     * 返回值：void：清空状态管理库和本地存储中的嘉宾会话。
     * 异常：本地存储删除失败时会被内部捕获，不影响内存状态清空。
     */
    clearGuest(): void {
      this.guest = undefined
      removeStoredSession(STORAGE_KEYS.guest)
    },
    /**
     * 清除工作人员端 Mock 会话。
     *
     * 入参：无。
     * 返回值：void：清空状态管理库和本地存储中的工作人员会话。
     * 异常：本地存储删除失败时会被内部捕获，不影响内存状态清空。
     */
    clearStaff(): void {
      this.staff = undefined
      removeStoredSession(STORAGE_KEYS.staff)
    },
  },
})
