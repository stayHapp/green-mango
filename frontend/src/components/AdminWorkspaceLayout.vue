<template>
  <section class="admin-workspace-shell">
    <aside class="admin-workspace-sidebar" aria-label="管理员会议导航">
      <router-link class="admin-workspace-brand" to="/admin/meetings">
        <span class="admin-workspace-brand__mark">知</span>
        <span>
          <strong>知会管理后台</strong>
          <small>会议与研讨活动</small>
        </span>
      </router-link>

      <div v-if="isMeetingWorkspace" class="admin-workspace-meeting-card">
        <span>当前会议</span>
        <strong>{{ meetingTitle }}</strong>
        <em>{{ meetingStatus || '筹备中' }}</em>
      </div>

      <nav class="admin-workspace-nav">
        <button
          v-for="item in menuItems"
          :key="item.key"
          type="button"
          class="admin-workspace-nav__item"
          :class="{ 'is-active': activeSection === item.key }"
          @click="handleMenuSelect(item.key)"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="admin-workspace-sidebar__footer">
        <button v-if="isMeetingWorkspace" type="button" @click="openGuestEntry">
          <el-icon><Monitor /></el-icon>
          <span>查看嘉宾端</span>
        </button>
        <button type="button" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </button>
      </div>
    </aside>

    <div class="admin-workspace-main">
      <header class="admin-workspace-topbar">
        <div class="admin-workspace-breadcrumb">
          <button v-if="isMeetingWorkspace" type="button" @click="goMeetings">
            <el-icon><ArrowLeft /></el-icon>
            会议管理
          </button>
          <span v-if="isMeetingWorkspace">/</span>
          <strong>{{ meetingTitle || '会议管理' }}</strong>
        </div>
        <div class="admin-workspace-user">
          <span class="admin-workspace-user__avatar">{{ adminInitial }}</span>
          <span>
            <strong>{{ session.admin?.name || '系统管理员' }}</strong>
            <small>管理员</small>
          </span>
        </div>
      </header>

      <main class="admin-workspace-content">
        <slot />
      </main>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowLeft,
  Calendar,
  Document,
  Grid,
  Monitor,
  Setting,
  SwitchButton,
  Tickets,
  User,
  UserFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { logoutClientSession } from '../api/sessions'
import { useSessionStore } from '../stores/session'

interface AdminMenuItem {
  key: string
  label: string
  icon: Component
}

const props = withDefaults(defineProps<{
  meetingId?: string
  meetingTitle?: string
  meetingStatus?: string
  activeSection: string
}>(), {
  meetingId: '',
  meetingTitle: '',
  meetingStatus: '',
})

const emit = defineEmits<{
  navigate: [section: string]
}>()

const router = useRouter()
const session = useSessionStore()
const isMeetingWorkspace = computed(isMeetingWorkspacePage)
const menuItems = computed(resolveMenuItems)
const adminInitial = computed(resolveAdminInitial)

/**
 * 判断当前布局是否绑定了某一场会议。
 *
 * 入参：无；函数读取组件传入的会议 ID。
 * 返回值：boolean：存在非空会议 ID 时返回 true，否则返回 false。
 * 异常：当前函数不主动抛出异常。
 */
function isMeetingWorkspacePage(): boolean {
  return Boolean(props.meetingId)
}

/**
 * 根据页面是否处于会议详情生成对应的左侧导航项。
 *
 * 入参：无；函数读取当前会议上下文。
 * 返回值：AdminMenuItem[]：会议列表页仅提供会议管理，会议详情页提供会议级管理入口。
 * 异常：当前函数不主动抛出异常。
 */
function resolveMenuItems(): AdminMenuItem[] {
  if (!isMeetingWorkspace.value) {
    return [{ key: 'meetings', label: '会议管理', icon: Calendar }]
  }

  return [
    { key: 'overview', label: '数据总览', icon: Grid },
    { key: 'edit', label: '会议信息', icon: Setting },
    { key: 'guests', label: '嘉宾管理', icon: User },
    { key: 'fields', label: '嘉宾字段', icon: Tickets },
    { key: 'assistant', label: '会议服务', icon: Document },
    { key: 'staff', label: '工作人员', icon: UserFilled },
    { key: 'checkins', label: '签到记录', icon: Calendar },
  ]
}

/**
 * 提取当前管理员姓名的首个可见字符，用于顶部头像。
 *
 * 入参：无；函数读取管理员会话。
 * 返回值：string：管理员姓名首字，未登录时返回“管”。
 * 异常：当前函数不主动抛出异常。
 */
function resolveAdminInitial(): string {
  return session.admin?.name.trim().charAt(0) || '管'
}

/**
 * 处理左侧菜单选择并通知父页面切换内容区域。
 *
 * 入参：section 为菜单对应的页面区块标识，必填。
 * 返回值：void：发出 `navigate` 事件，列表页同时回到会议列表路由。
 * 异常：当前函数不主动抛出异常。
 */
function handleMenuSelect(section: string): void {
  if (!isMeetingWorkspace.value) {
    void router.push('/admin/meetings')
    return
  }
  emit('navigate', section)
}

/**
 * 返回管理员可管理的会议列表。
 *
 * 入参：无。
 * 返回值：void：触发前端路由跳转。
 * 异常：当前函数不主动抛出异常。
 */
function goMeetings(): void {
  void router.push('/admin/meetings')
}

/**
 * 在新窗口打开当前会议的嘉宾公开入口。
 *
 * 入参：无；函数读取传入会议 ID。
 * 返回值：void：有会议 ID 时打开对应公开会议页。
 * 异常：浏览器阻止弹窗时当前函数不主动抛出异常。
 */
function openGuestEntry(): void {
  if (!props.meetingId) {
    return
  }
  window.open(`/meetings/${props.meetingId}`, '_blank', 'noopener,noreferrer')
}

/**
 * 退出管理员会话并返回统一登录页。
 *
 * 入参：无。
 * 返回值：Promise<void>：无论服务端撤销是否成功，最终清理本地管理员会话。
 * 异常：服务端异常会被转换为提示，不继续向外抛出。
 */
async function handleLogout(): Promise<void> {
  try {
    await logoutClientSession('admin')
  } catch {
    ElMessage.warning('服务端会话可能已失效，本地登录状态已清除。')
  } finally {
    session.clearRole('admin')
    await router.push('/login')
  }
}
</script>
