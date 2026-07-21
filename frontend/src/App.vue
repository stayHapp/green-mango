<template>
  <el-container class="app-shell" :class="{ 'staff-app-shell': isStaffPage, 'admin-app-shell': isAdminPage }">
    <el-header v-if="!isGuestPage && !isStaffWorkspace && !isAdminPage" class="topbar" :class="{ 'staff-topbar': isStaffPage }">
      <router-link class="brand" to="/">
        <span class="brand-name">知会</span>
        <span class="brand-subtitle">会议与签到原型</span>
      </router-link>
      <nav class="topnav">
        <template v-if="currentClient">
          <span v-if="!isStaffPage" class="current-client">{{ currentClient }}</span>
          <el-button text type="primary" @click="handleLogout">退出登录</el-button>
        </template>
        <template v-else>
          <router-link to="/login">管理与签到登录</router-link>
          <router-link to="/guest/login">嘉宾登录</router-link>
        </template>
      </nav>
    </el-header>
    <el-main :class="{ 'guest-main': isGuestPage, 'staff-main': isStaffPage, 'admin-main': isAdminPage }">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import { logoutClientSession } from './api/sessions'
import { useSessionStore } from './stores/session'
import type { ClientRole } from './types'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const currentClient = computed(clientName)
const isGuestPage = computed(guestPage)
const isStaffPage = computed(staffPage)
const isStaffWorkspace = computed(staffWorkspace)
const isAdminPage = computed(adminPage)

/**
 * 判断当前路由是否属于嘉宾端页面。
 *
 * 入参：无；函数读取当前路由路径。
 * 返回值：boolean：嘉宾登录、会议公开入口或报名页面返回 true，否则返回 false。
 * 异常：当前函数不主动抛出异常。
 */
function guestPage(): boolean {
  return route.path.startsWith('/guest/') || route.path.startsWith('/meetings/')
}

/**
 * 判断当前路由是否属于工作人员端页面。
 *
 * 入参：无；函数读取当前路由路径。
 * 返回值：boolean：路径以 `/staff/` 开头时返回 true，否则返回 false。
 * 异常：当前函数不主动抛出异常。
 */
function staffPage(): boolean {
  return route.path.startsWith('/staff/')
}

/**
 * 判断当前路由是否为采用独立移动端顶栏的工作人员签到工作台。
 *
 * 入参：无；函数读取当前路由名称。
 * 返回值：boolean：工作人员签到路由返回 true，否则返回 false。
 * 异常：当前函数不主动抛出异常。
 */
function staffWorkspace(): boolean {
  return route.name === 'staff-check-in'
}

/**
 * 判断当前路由是否属于管理员端页面。
 *
 * 入参：无；函数读取当前路由路径。
 * 返回值：boolean：路径以 `/admin/` 开头时返回 true，否则返回 false。
 * 异常：当前函数不主动抛出异常。
 */
function adminPage(): boolean {
  return route.path.startsWith('/admin/')
}

/**
 * 根据当前路由识别已登录的客户端名称。
 *
 * 入参：无；函数读取当前路由路径及对应会话状态。
 * 返回值：string：当前客户端名称；未登录或非客户端页面时返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
function clientName(): string {
  if (route.path.startsWith('/admin/') && session.admin) {
    return '管理员端'
  }

  if (route.path.startsWith('/staff/') && session.staff) {
    return '工作人员端'
  }

  if (route.path.startsWith('/guest/') && session.guest) {
    return '嘉宾端'
  }

  return ''
}

/**
 * 撤销当前服务端会话、清理本地状态并跳转至对应登录入口。
 *
 * 入参：无；函数根据当前路由确定需要清除的会话。
 * 返回值：Promise<void>：无论服务端是否可达，最终都会清理本地会话并完成跳转。
 * 异常：服务端撤销失败时显示提示，但异常不会继续向外抛出。
 */
async function handleLogout(): Promise<void> {
  const role: ClientRole = route.path.startsWith('/admin/')
    ? 'admin'
    : route.path.startsWith('/staff/')
      ? 'staff'
      : 'guest'
  const guestMeetingId = role === 'guest' ? session.guest?.meetingId : undefined
  try {
    await logoutClientSession(role)
  } catch {
    ElMessage.warning('服务端会话可能已失效，本地登录状态已清除。')
  } finally {
    session.clearRole(role)
    await router.push(
      role === 'guest'
        ? { path: '/guest/login', query: guestMeetingId ? { meetingId: guestMeetingId } : {} }
        : '/login',
    )
  }
}
</script>
