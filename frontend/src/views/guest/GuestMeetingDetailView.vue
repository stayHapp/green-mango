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
          <div class="guest-home-toolbar">
            <button
              type="button"
              class="guest-home-menu-button"
              aria-label="打开会议服务"
              @click="openServiceDrawer"
            >
              <svg class="guest-home-menu-button__icon" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M5 7h14M5 12h14M5 17h14" />
              </svg>
            </button>
            <el-button
              class="guest-home-logout-button"
              :loading="loggingOut"
              @click="handleGuestLogout"
            >
              <svg class="guest-home-logout-button__icon" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M10 5H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4M14 8l4 4-4 4M18 12H9" />
              </svg>
              退出
            </el-button>
          </div>

          <GuestMeetingSummary :meeting="meeting" compact />

          <section class="guest-home-card guest-pass-card guest-profile-card" aria-labelledby="guest-identity-title">
            <div class="guest-profile-card__avatar" aria-hidden="true">
              {{ (isGuestFieldVisible('name') ? session.guest.name : '嘉宾').slice(0, 1) }}
            </div>
            <div class="guest-pass-card__identity">
              <div class="guest-pass-card__name-row">
                <h2 id="guest-identity-title">{{ isGuestFieldVisible('name') ? session.guest.name : '参会嘉宾' }}</h2>
                <el-tag v-if="isGuestFieldVisible('tag') && session.guest.tag" class="identity-role" type="success" effect="light">
                  {{ session.guest.tag || '嘉宾' }}
                </el-tag>
              </div>
              <dl class="guest-pass-card__details">
                <div v-if="isGuestFieldVisible('organization') && session.guest.organization">
                  <dt>单位</dt>
                  <dd>{{ session.guest.organization }}</dd>
                </div>
                <div v-if="isGuestFieldVisible('title') && session.guest.title">
                  <dt>职位</dt>
                  <dd>{{ session.guest.title }}</dd>
                </div>
                <div v-if="isGuestFieldVisible('phone') && maskedPhone">
                  <dt>电话</dt>
                  <dd>{{ maskedPhone }}</dd>
                </div>
                <div v-for="item in visibleDynamicDetails" :key="item.key">
                  <dt>{{ item.label }}</dt>
                  <dd>{{ item.value }}</dd>
                </div>
              </dl>
            </div>

            <div v-if="isGuestFieldVisible('seat') && session.guest.seat" class="guest-pass-card__seat">
              <span>座位</span>
              <strong>{{ session.guest.seat }}</strong>
            </div>

          </section>

          <section class="guest-home-card guest-check-in-card" aria-label="签到凭证">
            <GuestQrCode :meeting-id="meeting.id" :token="session.guest.qrToken" compact />
          </section>

        </template>
      </main>

      <el-drawer
        v-if="meeting"
        v-model="serviceDrawerVisible"
        class="guest-service-drawer-shell"
        direction="ltr"
        size="min(420px, 88vw)"
        title="会议服务"
        :show-close="false"
        :with-header="false"
        append-to-body
        destroy-on-close
        @closed="handleServiceDrawerClosed"
      >
        <aside class="guest-service-drawer" aria-label="会议服务菜单">
          <header class="guest-service-drawer__header">
            <div>
              <h2>{{ meeting.title }}</h2>
              <p>会议服务</p>
            </div>
            <button type="button" aria-label="关闭会议服务" @click="closeServiceDrawer">
              <el-icon><Close /></el-icon>
            </button>
          </header>

          <div class="guest-service-drawer__content">
            <MeetingAssistantShortcutGrid
              :meeting-id="meeting.id"
              variant="drawer"
              @select="handleServiceSelected"
            />
          </div>

          <footer class="guest-service-drawer__footer">
            <button type="button" @click="returnToMeetingEntry">
              <el-icon><House /></el-icon>
              返回活动首页
            </button>
          </footer>
        </aside>
      </el-drawer>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Close, House } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

import { getApiErrorMessage } from '../../api/client'
import { getGuestMeeting } from '../../api/guestMeetings'
import { logoutClientSession } from '../../api/sessions'
import GuestQrCode from '../../components/GuestQrCode.vue'
import GuestMeetingSummary from '../../components/GuestMeetingSummary.vue'
import MeetingAssistantShortcutGrid from '../../components/MeetingAssistantShortcutGrid.vue'
import { useSessionStore } from '../../stores/session'
import type { Meeting, MeetingAssistantFeatureKey } from '../../types'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const loading = ref(false)
const loggingOut = ref(false)
const serviceDrawerVisible = ref(route.query.services === 'open')
const errorMessage = ref('')
const maskedPhone = computed(maskGuestPhone)
const visibleGuestFieldSet = computed(() => new Set(session.guest?.visibleFields ?? ['name', 'phone', 'organization', 'title', 'tag', 'seat']))
const visibleDynamicDetails = computed(buildVisibleDynamicDetails)

interface GuestDynamicDetail {
  key: string
  label: string
  value: string
}

/**
 * 打开嘉宾首页左侧会议服务抽屉。
 *
 * 入参：无；由左上角菜单按钮触发。
 * 返回值：void：将抽屉可见状态设置为 true。
 * 异常：当前函数不主动抛出异常。
 */
function openServiceDrawer(): void {
  serviceDrawerVisible.value = true
}

/**
 * 关闭嘉宾首页左侧会议服务抽屉。
 *
 * 入参：无；由抽屉关闭按钮触发。
 * 返回值：void：将抽屉可见状态设置为 false。
 * 异常：当前函数不主动抛出异常。
 */
function closeServiceDrawer(): void {
  serviceDrawerVisible.value = false
}

/**
 * 在会议服务抽屉完全关闭后清理路由中的自动打开标记。
 *
 * 入参：无；函数读取当前路由的 services 查询参数。
 * 返回值：Promise<void>：存在自动打开标记时完成无历史记录的路由替换，否则直接结束。
 * 异常：路由替换失败时由 Vue Router 抛出异常。
 */
async function handleServiceDrawerClosed(): Promise<void> {
  if (route.query.services !== 'open') {
    return
  }

  await router.replace({ path: route.path })
}

/**
 * 在选择会议服务后收起抽屉，让服务组件继续完成详情页跳转。
 *
 * 入参：key 为已选择的会议服务标识，必填；当前仅用于保持事件契约清晰。
 * 返回值：void：关闭当前抽屉。
 * 异常：当前函数不主动抛出异常。
 */
function handleServiceSelected(key: MeetingAssistantFeatureKey): void {
  // 保留服务标识参数，便于后续按服务记录访问行为时直接扩展。
  void key
  serviceDrawerVisible.value = false
}

/**
 * 从会议服务抽屉返回当前会议的公开活动首页。
 *
 * 入参：无；函数读取已加载会议的 ID。
 * 返回值：Promise<void>：关闭抽屉并完成活动首页路由跳转。
 * 异常：会议尚未加载时直接结束；路由跳转失败时由 Vue Router 抛出异常。
 */
async function returnToMeetingEntry(): Promise<void> {
  if (!meeting.value) {
    return
  }
  serviceDrawerVisible.value = false
  await router.push(`/meetings/${meeting.value.id}`)
}

/**
 * 判断一个固定或扩展嘉宾字段是否允许在嘉宾端呈现。
 *
 * 入参：fieldKey 为字段 key，必填。
 * 返回值：boolean：管理员选择呈现时返回 true，否则返回 false。
 * 异常：当前函数不主动抛出异常。
 */
function isGuestFieldVisible(fieldKey: string): boolean {
  return visibleGuestFieldSet.value.has(fieldKey)
}

/**
 * 生成嘉宾首页需要呈现的非空动态字段列表。
 *
 * 入参：无；函数读取当前嘉宾的动态值、字段标签和会议呈现配置。
 * 返回值：GuestDynamicDetail[]：按资料响应顺序返回可见且有值的扩展字段。
 * 异常：当前函数不主动抛出异常；缺少标签时使用字段 key 作为兜底标题。
 */
function buildVisibleDynamicDetails(): GuestDynamicDetail[] {
  const values = session.guest?.values ?? {}
  const labels = session.guest?.fieldLabels ?? {}
  return Object.entries(values)
    .filter(([key, value]) => isGuestFieldVisible(key) && Boolean(value?.trim()))
    .map(([key, value]) => ({ key, label: labels[key] || key, value: value?.trim() || '' }))
}

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
    serviceDrawerVisible.value = route.query.services === 'open'
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
