<template>
  <section class="guest-entry-page">
    <div class="guest-home-shell">
      <main class="guest-entry-content">
        <div v-if="loading" v-loading="loading" class="page-loading-block guest-entry-loading" />

        <div v-else-if="errorMessage" class="guest-home-error">
          <el-alert type="error" :closable="false" :title="errorMessage" />
          <el-button type="primary" plain @click="loadMeeting">重新加载</el-button>
        </div>

        <template v-else-if="meeting">
          <GuestMeetingSummary :meeting="meeting" show-description />

          <section class="guest-entry-actions" aria-label="参会操作">
            <el-button class="guest-entry-primary-button" type="primary" size="large" @click="openGuestAccess">
              {{ hasCurrentSession ? '我的入场码' : '参会登录' }}
            </el-button>
            <el-button
              v-if="meeting.registrationEnabled"
              class="guest-entry-secondary-button"
              size="large"
              @click="openRegistration"
            >
              申请报名
            </el-button>
          </section>

          <section class="guest-entry-services" aria-labelledby="guest-entry-services-title">
            <div class="guest-entry-section-heading">
              <h2 id="guest-entry-services-title">会议服务</h2>
            </div>
            <div class="guest-entry-service-grid">
              <button v-for="item in serviceItems" :key="item.title" type="button" @click="openGuestAccess">
                <span><el-icon><component :is="item.icon" /></el-icon></span>
                <span class="guest-entry-service-grid__copy">
                  <strong>{{ item.title }}</strong>
                  <small>{{ item.description }}</small>
                </span>
                <el-icon class="guest-entry-service-grid__arrow"><ArrowRight /></el-icon>
              </button>
            </div>
          </section>

          <footer class="guest-entry-staff-access">
            <router-link :to="`/meetings/${meetingId}/staff/login`">工作人员入口</router-link>
          </footer>
        </template>
      </main>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, type Component } from 'vue'
import { ArrowRight, Calendar, Location, PhoneFilled, Reading, Sunny } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

import { getApiErrorMessage } from '../../api/client'
import { getPublicMeeting } from '../../api/sessions'
import GuestMeetingSummary from '../../components/GuestMeetingSummary.vue'
import { useSessionStore } from '../../stores/session'
import type { Meeting } from '../../types'

interface GuestEntryServiceItem {
  title: string
  description: string
  icon: Component
}

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const loading = ref(false)
const errorMessage = ref('')
const meetingId = computed(readMeetingId)
const hasCurrentSession = computed(hasCurrentGuestSession)
const serviceItems: GuestEntryServiceItem[] = [
  { title: '会议日程', description: '掌握活动安排', icon: Calendar },
  { title: '会议资料', description: '查看参会须知', icon: Reading },
  { title: '天气提醒', description: '提前规划行程', icon: Sunny },
  { title: '路线导航', description: '快速抵达会场', icon: Location },
  { title: '联系会务', description: '及时获得帮助', icon: PhoneFilled },
]

/**
 * 从当前会议入口路由读取会议 ID。
 *
 * 入参：无；函数读取路由参数 `id`。
 * 返回值：string：会议 ID 字符串，缺失时返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
function readMeetingId(): string {
  return route.params.id ? String(route.params.id) : ''
}

/**
 * 判断本地是否已有当前会议的嘉宾会话。
 *
 * 入参：无；函数读取当前会议 ID 与 Pinia（状态管理库）中的嘉宾会话。
 * 返回值：boolean：会话所属会议与当前入口一致时返回 true。
 * 异常：当前函数不主动抛出异常。
 */
function hasCurrentGuestSession(): boolean {
  return Boolean(meetingId.value && session.guest?.meetingId === meetingId.value)
}

/**
 * 加载会议专属入口可以公开展示的基础信息。
 *
 * 入参：无；函数读取当前路由会议 ID。
 * 返回值：Promise<void>：成功后更新会议内容和页面状态。
 * 异常：会议不存在、尚未发布或网络不可用时捕获异常并展示中文提示。
 */
async function loadMeeting(): Promise<void> {
  errorMessage.value = ''
  if (!meetingId.value) {
    meeting.value = undefined
    errorMessage.value = '缺少会议入口 ID，请通过会议专属链接进入。'
    return
  }
  loading.value = true
  try {
    meeting.value = await getPublicMeeting(meetingId.value)
  } catch (error) {
    meeting.value = undefined
    errorMessage.value = getApiErrorMessage(error, '会议入口不存在或尚未发布。')
  } finally {
    loading.value = false
  }
}

/**
 * 根据当前会话状态进入嘉宾中心或身份核验页。
 *
 * 入参：无；函数读取当前会议 ID 和嘉宾会话状态。
 * 返回值：Promise<void>：完成目标页面路由跳转。
 * 异常：路由导航失败时由 Vue Router 抛出异常。
 */
async function openGuestAccess(): Promise<void> {
  if (hasCurrentSession.value) {
    await router.push(`/guest/meetings/${meetingId.value}`)
    return
  }
  await router.push({ path: '/guest/login', query: { meetingId: meetingId.value } })
}

/**
 * 打开当前会议的公开自主报名页面。
 *
 * 入参：无；函数读取当前会议 ID。
 * 返回值：Promise<void>：完成报名页面路由跳转。
 * 异常：路由导航失败时由 Vue Router 抛出异常。
 */
async function openRegistration(): Promise<void> {
  await router.push(`/meetings/${meetingId.value}/register`)
}

onMounted(loadMeeting)
</script>
