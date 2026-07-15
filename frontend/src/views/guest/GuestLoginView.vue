<template>
  <section class="page guest-portal-page">
    <div class="guest-portal-page__inner">
    <el-button
      v-if="meeting && currentGuest"
      class="guest-logout-button"
      :icon="SwitchButton"
      circle
      aria-label="退出登录"
      title="退出登录"
      :loading="loggingOut"
      @click="handleGuestLogout"
    />
    <div v-if="meeting && currentGuest" class="guest-assistant-toolbar">
      <div v-show="assistantToolbarExpanded" class="guest-assistant-toolbar__actions">
        <el-button v-for="item in meetingAssistantFeatureDefinitions" :key="item.key" text @click="openAssistantFeature(item.key)">{{ item.title }}</el-button>
      </div>
      <el-button
        :icon="MenuIcon"
        circle
        aria-label="展开会议功能"
        title="会议功能"
        :aria-expanded="assistantToolbarExpanded"
        @click="toggleAssistantToolbar"
      />
    </div>
    <div v-if="meeting" class="guest-meeting-hero">
      <div>
        <h1>{{ meeting.title }}</h1>
        <dl class="compact-info-list">
          <dt>时间</dt>
          <dd>{{ formatDate(meeting.startTime) }} - {{ formatDate(meeting.endTime) }}</dd>
          <dt>地点</dt>
          <dd>{{ meeting.location }}</dd>
        </dl>
      </div>
    </div>
    <el-empty v-else description="未找到会议入口" />

    <el-card v-if="meeting && !currentGuest" shadow="never" class="form-card guest-login-card">
      <template #header>身份验证</template>
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="姓名">
          <el-input v-model="name" placeholder="请输入嘉宾姓名" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="phone" placeholder="请输入手机号" />
        </el-form-item>
        <div class="action-row">
          <el-button @click="fillDemoGuest">填入示例</el-button>
          <el-button type="primary" :loading="loading" @click="handleLogin">登录</el-button>
        </div>
      </el-form>
      <el-alert v-if="errorMessage" class="top-gap" type="error" :closable="false" :title="errorMessage" />
    </el-card>

    <div v-if="meeting && currentGuest" class="guest-content-stack">
      <el-card shadow="never" class="guest-pass-card">
        <div class="identity-panel">
          <div class="guest-identity-heading">
            <div class="identity-name">{{ currentGuest.name }}</div>
            <el-tag class="identity-role" type="success" effect="light">{{ currentGuest.tag }}</el-tag>
          </div>
        </div>
        <dl class="info-list">
          <dt>电话</dt>
          <dd>{{ currentGuest.phone }}</dd>
          <dt>单位</dt>
          <dd>{{ currentGuest.organization }}</dd>
          <dt>职务</dt>
          <dd>{{ currentGuest.title }}</dd>
          <dt>座位</dt>
          <dd>{{ currentGuest.seat }}</dd>
        </dl>
        <GuestQrCode :token="currentGuest.qrToken" />
      </el-card>

    </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Menu as MenuIcon, SwitchButton } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import { getApiErrorMessage } from '../../api/client'
import { meetingAssistantFeatureDefinitions } from '../../api/meetingAssistant'
import { getPublicMeeting, loginGuest, logoutClientSession } from '../../api/sessions'
import { useSessionStore } from '../../stores/session'
import type { Guest, Meeting, MeetingAssistantFeatureKey } from '../../types'
import GuestQrCode from '../../components/GuestQrCode.vue'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const name = ref('')
const phone = ref('')
const loading = ref(false)
const loggingOut = ref(false)
const errorMessage = ref('')
const assistantToolbarExpanded = ref(false)
const currentGuest = computed(() => {
  if (!meeting.value || session.guest?.meetingId !== meeting.value.id) {
    return undefined
  }

  return session.guest
})

/**
 * 嘉宾会话被清除时同步清空身份表单和功能提示。
 *
 * 入参：guest 为当前 Pinia 嘉宾状态；退出后为 undefined。
 * 返回值：void：只更新当前页面的敏感表单和提示状态。
 * 异常：当前函数不主动抛出异常。
 */
function clearIdentityAfterLogout(guest: Guest | undefined): void {
  if (guest) {
    return
  }
  name.value = ''
  phone.value = ''
  errorMessage.value = ''
  assistantToolbarExpanded.value = false
}

watch(() => session.guest, clearIdentityAfterLogout)

/**
 * 加载扫码入口对应的会议信息。
 *
 * 入参：
 *   无；函数读取 URL 中的 meetingId 参数，并调用公开会议 API。
 *
 * 返回值：
 *   Promise<void>：加载完成后更新页面会议信息。
 *
 * 异常：
 *   会议不存在、尚未发布或后端不可用时清空会议信息并展示错误提示。
 */
async function loadMeeting(): Promise<void> {
  const meetingId = route.query.meetingId ? String(route.query.meetingId) : ''

  if (!meetingId) {
    errorMessage.value = '缺少会议入口 ID，请通过会议二维码进入。'
    return
  }
  try {
    meeting.value = await getPublicMeeting(meetingId)
  } catch (error) {
    meeting.value = undefined
    errorMessage.value = getApiErrorMessage(error, '会议入口不存在或尚未发布。')
  }
}

/**
 * 填入本地联调嘉宾示例。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：只更新当前表单字段。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function fillDemoGuest(): void {
  name.value = '李文博'
  phone.value = '13900000001'
  errorMessage.value = ''
}

/**
 * 调用后端 API 完成嘉宾登录并读取完整个人资料。
 *
 * 入参：
 *   无；函数从页面表单中读取姓名和手机号，两个字段均必填。
 *
 * 返回值：
 *   Promise<void>：登录成功后保存嘉宾会话并跳转到嘉宾会议列表。
 *
 * 异常：
 *   身份不匹配、会议无效或网络异常时展示后端错误提示。
 */
async function handleLogin(): Promise<void> {
  errorMessage.value = ''

  if (!meeting.value) {
    errorMessage.value = '当前会议入口无效，无法登录。'
    return
  }

  if (!name.value.trim() || !phone.value.trim()) {
    errorMessage.value = '请填写姓名和手机号。'
    return
  }

  loading.value = true
  try {
    const result = await loginGuest(meeting.value.id, name.value.trim(), phone.value.trim())
    session.setGuest(result.user, result.access)
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '嘉宾登录失败，请检查姓名和手机号。')
  } finally {
    loading.value = false
  }
}

/**
 * 退出当前嘉宾会话并恢复身份验证页面。
 *
 * 入参：无；函数使用当前已登录的嘉宾会话。
 * 返回值：Promise<void>：无论服务端会话是否仍然有效，最终都会清除本地嘉宾状态。
 * 异常：服务端退出失败时显示说明提示，异常不会继续向外抛出。
 */
async function handleGuestLogout(): Promise<void> {
  loggingOut.value = true
  try {
    await logoutClientSession('guest')
    ElMessage.success('已退出登录。')
  } catch {
    ElMessage.warning('服务端会话可能已失效，本地登录状态已清除。')
  } finally {
    session.clearRole('guest')
    loggingOut.value = false
  }
}

/**
 * 展开或收起会议信息上方的单行功能入口。
 *
 * 入参：无。
 * 返回值：void：切换五项会议功能入口的可见状态。
 * 异常：当前函数不主动抛出异常。
 */
function toggleAssistantToolbar(): void {
  assistantToolbarExpanded.value = !assistantToolbarExpanded.value
}

/**
 * 从顶部快捷入口打开指定会议助手功能。
 *
 * 入参：key 为会议助手功能标识，必填。
 * 返回值：Promise<void>：跳转到对应功能独立页面并收起快捷入口。
 * 异常：路由导航失败时由 Vue Router 抛出异常。
 */
async function openAssistantFeature(key: MeetingAssistantFeatureKey): Promise<void> {
  assistantToolbarExpanded.value = false
  await router.push(`/guest/meetings/${meeting.value?.id ?? ''}/assistant/${key}`)
}

/**
 * 格式化日期时间展示。
 *
 * 入参：
 *   value：ISO 日期字符串，必填。
 *
 * 返回值：
 *   string：中文本地化日期时间文本。
 *
 * 异常：
 *   当前函数不主动抛出异常；非法日期会按浏览器默认结果展示。
 */
function formatDate(value: string): string {
  if (!value) {
    return '待定'
  }
  return new Date(value).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}

onMounted(loadMeeting)
</script>
