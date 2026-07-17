<template>
  <section class="guest-home-page">
    <div class="guest-home-shell">
      <main class="guest-home-content">
        <div v-if="loading" v-loading="loading" class="page-loading-block guest-home-loading" />

        <el-empty v-else-if="!session.guest" description="当前会议身份尚未核验">
          <el-button type="primary" @click="goLogin">前往身份核验</el-button>
        </el-empty>

        <div v-else-if="errorMessage" class="guest-home-error">
          <el-alert type="error" :closable="false" :title="errorMessage" />
          <el-button type="primary" plain @click="loadDetail">重新加载</el-button>
        </div>

        <template v-else-if="meeting">
          <GuestMeetingSummary :meeting="meeting" />

          <section class="guest-home-card guest-pass-card" aria-labelledby="guest-identity-title">
            <div class="guest-pass-card__identity">
              <div class="guest-pass-card__name-row">
                <h2 id="guest-identity-title">{{ session.guest.name }}</h2>
                <el-tag class="identity-role" type="success" effect="light">
                  {{ session.guest.tag || '嘉宾' }}
                </el-tag>
              </div>
              <dl class="guest-pass-card__details">
                <div v-if="session.guest.organization">
                  <dt>单位</dt>
                  <dd>{{ session.guest.organization }}</dd>
                </div>
                <div v-if="session.guest.title">
                  <dt>职位</dt>
                  <dd>{{ session.guest.title }}</dd>
                </div>
                <div v-if="maskedPhone">
                  <dt>电话</dt>
                  <dd>{{ maskedPhone }}</dd>
                </div>
              </dl>
            </div>

            <div v-if="session.guest.seat" class="guest-pass-card__seat">
              <span>座位</span>
              <strong>{{ session.guest.seat }}</strong>
            </div>

            <div class="guest-pass-card__check-in" aria-label="签到">
              <GuestQrCode :meeting-id="meeting.id" :token="session.guest.qrToken" compact />
            </div>
          </section>

          <section class="guest-service-card" aria-labelledby="guest-service-title">
            <h2 id="guest-service-title">会议服务</h2>
            <MeetingAssistantShortcutGrid :meeting-id="meeting.id" />
          </section>

          <footer class="guest-home-footer">
            <el-button text :loading="loggingOut" @click="handleGuestLogout">退出登录</el-button>
          </footer>
        </template>
      </main>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import { getApiErrorMessage } from '../../api/client'
import { getGuestMeeting } from '../../api/guestMeetings'
import { logoutClientSession } from '../../api/sessions'
import GuestQrCode from '../../components/GuestQrCode.vue'
import GuestMeetingSummary from '../../components/GuestMeetingSummary.vue'
import MeetingAssistantShortcutGrid from '../../components/MeetingAssistantShortcutGrid.vue'
import { useSessionStore } from '../../stores/session'
import type { Meeting } from '../../types'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const loading = ref(false)
const loggingOut = ref(false)
const errorMessage = ref('')
const maskedPhone = computed(maskGuestPhone)

/**
 * 加载会话所属的当前会议详情，并阻止会议级嘉宾身份访问其他会议。
 *
 * 入参：无；函数读取当前路由会议 ID 和 Pinia（状态管理库）中的嘉宾会议 ID。
 * 返回值：Promise<void>：成功后更新当前会议；路径不匹配时替换为会话所属会议。
 * 异常：会话失效、会议不存在或网络失败时捕获异常并展示中文提示。
 */
async function loadDetail(): Promise<void> {
  if (!session.guest) {
    meeting.value = undefined
    return
  }

  let routeMeetingId = String(route.params.id)
  if (routeMeetingId !== session.guest.meetingId) {
    // 嘉宾是会议级身份，发现跨会议路径时回到会话所属会议。
    await router.replace(`/guest/meetings/${session.guest.meetingId}`)
    routeMeetingId = session.guest.meetingId
  }

  loading.value = true
  errorMessage.value = ''
  try {
    meeting.value = await getGuestMeeting(routeMeetingId)
  } catch (error) {
    meeting.value = undefined
    errorMessage.value = getApiErrorMessage(error, '当前会议信息加载失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

/**
 * 跳转到当前路由会议对应的嘉宾身份核验入口。
 *
 * 入参：无；函数读取路由中的会议 ID。
 * 返回值：Promise<void>：完成嘉宾登录页跳转。
 * 异常：路由跳转失败时由 Vue Router 抛出异常。
 */
async function goLogin(): Promise<void> {
  await router.replace(`/guest/login?meetingId=${String(route.params.id)}`)
}

/**
 * 撤销嘉宾服务端会话并返回当前会议身份核验入口。
 *
 * 入参：无；函数使用当前嘉宾访问凭证和会议 ID。
 * 返回值：Promise<void>：无论服务端撤销是否成功，都会清理本地会话并返回登录页。
 * 异常：服务端撤销失败时显示警告但不继续向外抛出。
 */
async function handleGuestLogout(): Promise<void> {
  const meetingId = session.guest?.meetingId || String(route.params.id)
  loggingOut.value = true
  try {
    await logoutClientSession('guest')
    ElMessage.success('已退出登录。')
  } catch {
    ElMessage.warning('服务端会话可能已失效，本地登录状态已清除。')
  } finally {
    session.clearRole('guest')
    loggingOut.value = false
    await router.replace(`/guest/login?meetingId=${meetingId}`)
  }
}

/**
 * 将嘉宾手机号转换为适合首页展示的脱敏形式。
 *
 * 入参：无；函数读取当前会议级嘉宾的手机号。
 * 返回值：string：常规手机号隐藏中间四位，短号码隐藏中间字符，空值返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
function maskGuestPhone(): string {
  const phone = session.guest?.phone.trim() || ''
  if (!phone) {
    return ''
  }
  if (phone.length >= 7) {
    return `${phone.slice(0, 3)}****${phone.slice(-4)}`
  }
  if (phone.length <= 2) {
    return '*'.repeat(phone.length)
  }
  return `${phone.slice(0, 1)}${'*'.repeat(phone.length - 2)}${phone.slice(-1)}`
}

onMounted(loadDetail)
</script>
