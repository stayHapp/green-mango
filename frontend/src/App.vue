<template>
  <el-container class="app-shell">
    <el-header class="topbar">
      <router-link class="brand" to="/">
        <span class="brand-name">知会</span>
        <span class="brand-subtitle">会议与签到原型</span>
      </router-link>
      <nav class="topnav">
        <template v-if="currentClient">
          <span class="current-client">{{ currentClient }}</span>
          <el-button text type="primary" @click="handleLogout">退出登录</el-button>
        </template>
        <template v-else>
          <router-link to="/login">管理与签到登录</router-link>
          <router-link to="/guest/login?meetingId=m-edu-2026">嘉宾登录</router-link>
        </template>
      </nav>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useSessionStore } from './stores/session'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const currentClient = computed(clientName)

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
 * 退出当前客户端的本地 Mock 会话并跳转至对应登录入口。
 *
 * 入参：无；函数根据当前路由确定需要清除的会话。
 * 返回值：void：清除会话后完成前端路由跳转。
 * 异常：当前函数不主动抛出异常。
 */
function handleLogout(): void {
  if (route.path.startsWith('/admin/')) {
    session.clearAdmin()
    router.push('/login')
    return
  }

  if (route.path.startsWith('/staff/')) {
    session.clearStaff()
    router.push('/login')
    return
  }

  session.clearGuest()
  router.push('/guest/login')
}
</script>
