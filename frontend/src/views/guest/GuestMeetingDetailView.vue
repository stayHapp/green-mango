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
          <header class="guest-home-toolbar">
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
            <button
              type="button"
              class="guest-home-logout-button"
              :disabled="loggingOut"
              aria-label="退出登录"
              @click="handleGuestLogout"
            >
              <svg class="guest-home-logout-button__icon" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M14 8l4 4-4 4M18 12H9" />
              </svg>
              退出
            </button>
          </header>


          <div class="who">
            <span class="who__name">{{ isGuestFieldVisible('name') ? session.guest.name : '参会嘉宾' }}</span>
            <span v-if="isGuestFieldVisible('tag') && session.guest.tag" class="badge-vip">
              {{ session.guest.tag || '嘉宾' }}
            </span>
          </div>

          <div class="fields">
            <div
              v-if="isGuestFieldVisible('organization') && session.guest.organization"
              class="f-row"
              data-field="unit"
            >
              <span class="fl">单位</span>
              <span class="fv">{{ session.guest.organization }}</span>
            </div>
            <div
              v-if="isGuestFieldVisible('title') && session.guest.title"
              class="f-row"
              data-field="title"
            >
              <span class="fl">职位</span>
              <span class="fv">{{ session.guest.title }}</span>
            </div>
            <div
              v-if="isGuestFieldVisible('phone') && maskedPhone"
              class="f-row"
              data-field="phone"
            >
              <span class="fl">电话</span>
              <span class="fv">{{ maskedPhone }}</span>
            </div>
            <div v-for="item in visibleDynamicDetails" :key="item.key" class="f-row">
              <span class="fl">{{ item.label }}</span>
              <span class="fv">{{ item.value }}</span>
            </div>
            <div
              v-if="isGuestFieldVisible('seat') && session.guest.seat"
              class="f-row"
              data-field="seat"
            >
              <span class="fl">座位</span>
              <span class="fv seat">{{ session.guest.seat }}</span>
            </div>
          </div>

          <div v-if="isCheckedIn" class="zone">
            <div class="done-ck" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <div class="st">已签到</div>
            <div class="tm">签到时间 {{ formattedCheckInTime }}</div>
          </div>

          <div v-else class="qr-zone">
            <span class="pill">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true">
                <circle cx="12" cy="12" r="9" />
                <polyline points="12 7 12 12 15 14" />
              </svg>
              未签到 · 待核验
            </span>
            <div class="qr-box">
              <GuestQrCode :meeting-id="meeting.id" :token="session.guest.qrToken" compact />
            </div>
            <div class="tip">请向工作人员出示二维码，<b>扫码完成签到</b></div>
          </div>
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
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Close, House } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

import { getApiErrorMessage } from '../../api/client'
import { getGuestMeeting } from '../../api/guestMeetings'
import { getGuestCheckInQr, getGuestProfile, logoutClientSession } from '../../api/sessions'
import GuestQrCode from '../../components/GuestQrCode.vue'
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
// 已从签到二维码接口读取；为空时默认呈现"未签到 + 二维码"分支。
const checkInTimeText = ref('')
const checkInStatusLoading = ref(false)

const maskedPhone = computed(maskGuestPhone)
const visibleGuestFieldSet = computed(
  () => new Set(session.guest?.visibleFields ?? ['name', 'phone', 'organization', 'title', 'tag', 'seat']),
)
const visibleDynamicDetails = computed(buildVisibleDynamicDetails)
const isCheckedIn = computed(() => Boolean(checkInTimeText.value))
const formattedCheckInTime = computed(() => formatCheckInTime(checkInTimeText.value))

interface GuestDynamicDetail {
  key: string
  label: string
  value: string
}

/**
 * 把签到时间格式化为首页展示所需的 YYYY/MM/DD HH:MM。
 */
function formatCheckInTime(value: string): string {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const yyyy = date.getFullYear()
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const dd = String(date.getDate()).padStart(2, '0')
  const hh = String(date.getHours()).padStart(2, '0')
  const mi = String(date.getMinutes()).padStart(2, '0')
  return `${yyyy}/${mm}/${dd} ${hh}:${mi}`
}

/**
 * 打开嘉宾首页左侧会议服务抽屉。
 */
function openServiceDrawer(): void {
  serviceDrawerVisible.value = true
}

/**
 * 关闭嘉宾首页左侧会议服务抽屉。
 */
function closeServiceDrawer(): void {
  serviceDrawerVisible.value = false
}

/**
 * 在会议服务抽屉完全关闭后清理路由中的自动打开标记。
 */
async function handleServiceDrawerClosed(): Promise<void> {
  if (route.query.services !== 'open') {
    return
  }
  await router.replace({ path: route.path })
}

/**
 * 在选择会议服务后收起抽屉。
 */
function handleServiceSelected(key: MeetingAssistantFeatureKey): void {
  void key
  serviceDrawerVisible.value = false
}

/**
 * 从会议服务抽屉返回当前会议的公开活动首页。
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
 */
function isGuestFieldVisible(fieldKey: string): boolean {
  return visibleGuestFieldSet.value.has(fieldKey)
}

/**
 * 生成嘉宾首页需要呈现的非空动态字段列表。
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
 */
async function loadDetail(): Promise<void> {
  if (!session.guest) {
    meeting.value = undefined
    return
  }

  let routeMeetingId = String(route.params.id)
  if (routeMeetingId !== session.guest.meetingId) {
    await router.replace(`/guest/meetings/${session.guest.meetingId}`)
    routeMeetingId = session.guest.meetingId
  }

  loading.value = true
  errorMessage.value = ''
  try {
    const [meetingData, profile] = await Promise.all([
      getGuestMeeting(routeMeetingId),
      getGuestProfile(routeMeetingId),
    ])
    meeting.value = meetingData
    // 刷新字段显隐与资料，确保后台调整后无需重新登录即可生效。
    if (session.guestAccess) {
      session.setGuest(profile, session.guestAccess)
    }
    serviceDrawerVisible.value = route.query.services === 'open'
    await loadCheckInStatus(routeMeetingId)
  } catch (error) {
    meeting.value = undefined
    errorMessage.value = getApiErrorMessage(error, '当前会议信息加载失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

/**
 * 读取当前嘉宾在本场会议中的签到状态，驱动已签到/未签到分支。
 *
 * 入参：meetingId 为数字会议 ID 字符串，必填。
 * 返回值：Promise<void>：成功时更新 checkInTimeText；失败时保持空值，呈现未签到分支。
 * 异常：网络或会话失败时不抛出到页面，只保留空状态并打印错误提示。
 */
async function loadCheckInStatus(meetingId: string): Promise<void> {
  checkInStatusLoading.value = true
  try {
    const status = await getGuestCheckInQr(meetingId)
    checkInTimeText.value = status.isCheckedIn ? status.checkedInAt || '已签到' : ''
  } catch {
    // 签到状态读取失败时不阻断首页其他信息展示，默认进入未签到分支。
    checkInTimeText.value = ''
  } finally {
    checkInStatusLoading.value = false
  }
}

/**
 * 跳转到当前路由会议对应的嘉宾身份核验入口。
 */
async function goLogin(): Promise<void> {
  await router.replace(`/guest/login?meetingId=${String(route.params.id)}`)
}

/**
 * 撤销嘉宾服务端会话并返回当前会议身份核验入口。
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

onMounted(() => {
  loadDetail()
  // 后台修改嘉宾字段或签到状态后，嘉宾端可能停留在原页面。
  // 当页面重新可见或获得焦点时自动重新拉取，主持人无需提醒嘉宾手动刷新。
  document.addEventListener('visibilitychange', handleVisibilityRefresh)
  window.addEventListener('focus', handleVisibilityRefresh)
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', handleVisibilityRefresh)
  window.removeEventListener('focus', handleVisibilityRefresh)
})

/**
 * 嘉宾端页面恢复可见时重新拉取最新嘉宾资料与签到状态。
 */
function handleVisibilityRefresh(): void {
  if (document.visibilityState !== 'visible') return
  if (!session.guest || !meeting.value) return
  void loadDetail()
}
</script>

<style scoped>
.guest-home-page {
  --green-accent: #0d6b4a;
  --green-strong: #0a553c;
  --green-mid-2: #12805a;
  --green-chip: #0f7a55;
  --green-deep: #1a3a2e;
  --green-mid: #2d5a4a;
  --green-brand: #3d6f5c;
  --text-title: #142c21;
  --text-sub: #3d5c4d;
  --text-muted: #8ba295;
  --text-soft: #7a8f84;
  --line: #e2ebe5;
  --pill-bg: #fdf3dd;
  --pill-border: #f0dba8;
  --pill-text: #9a6a10;
  --frame-border: #b9d4c4;
  --frame-bg: #fbfdfc;
  --amber-text: #8a5b12;
  --amber-grad-start: #fbe8bd;
  --amber-grad-end: #f5d38a;
  --screen-bg: #f4f7f5;

  position: relative;
  min-height: 100vh;
  min-height: 100dvh;
  width: 100%;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(1000px 600px at 15% 10%, rgba(18, 120, 84, 0.16), transparent 60%),
    radial-gradient(900px 700px at 88% 85%, rgba(9, 84, 58, 0.20), transparent 60%),
    linear-gradient(150deg, #f2f7f4 0%, #e6efe9 55%, #dfe9e2 100%);
  color: var(--text-title);
  font-family: "PingFang SC", "HarmonyOS Sans SC", "Microsoft YaHei", sans-serif;
  box-sizing: border-box;
}

.guest-home-shell {
  flex: 1;
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  background: var(--screen-bg);
  position: relative;
  overflow: hidden;
  box-shadow: 0 24px 64px -32px rgba(20, 50, 35, 0.22);
}

.guest-home-content {
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.guest-home-loading,
.guest-home-error {
  margin: 80px auto;
  max-width: 360px;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  text-align: center;
}

/* 顶栏：汉堡按钮与退出按钮均为无边框轻量样式 */
.guest-home-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
  height: 54px;
  flex: none;
}

.guest-home-menu-button {
  width: 38px;
  height: 38px;
  border: none;
  background: transparent;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.18s;
}

.guest-home-menu-button:hover {
  background: rgba(13, 107, 74, 0.08);
}

.guest-home-menu-button__icon {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: var(--text-title);
  stroke-width: 2.2;
  stroke-linecap: round;
}

.guest-home-logout-button {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
  color: var(--text-sub);
  border: none;
  background: transparent;
  padding: 8px 6px;
  cursor: pointer;
  font-family: inherit;
  transition: color 0.18s;
}

.guest-home-logout-button:hover {
  color: var(--green-accent);
}

.guest-home-logout-button[disabled] {
  opacity: 0.65;
  cursor: not-allowed;
}

.guest-home-logout-button__icon {
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* 会议名称：居中标题 */
.conf-title {
  text-align: center;
  margin-top: 2px;
  font-size: 17.5px;
  font-weight: 700;
  color: var(--text-title);
  letter-spacing: 0.5px;
  padding: 0 18px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: none;
}

/* 姓名区：居中大字 + 徽章 */
.who {
  position: relative;
  text-align: center;
  margin-top: 10px;
  flex: none;
}

.who__name {
  display: inline-block;
  font-size: 27px;
  font-weight: 700;
  color: var(--text-title);
  letter-spacing: 1px;
}

.badge-vip {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  margin-left: 10px;
  font-size: 11px;
  font-weight: 600;
  color: var(--amber-text);
  background: linear-gradient(120deg, var(--amber-grad-start), var(--amber-grad-end));
  padding: 3px 9px;
  border-radius: 6px;
  letter-spacing: 1px;
  white-space: nowrap;
}

/* 信息列表 */
.fields {
  margin: 20px 34px 0;
  flex: none;
}

.f-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 13px 4px;
  border-bottom: 1px solid var(--line);
}

.f-row .fl {
  font-size: 13px;
  color: var(--text-muted);
  letter-spacing: 1px;
  flex: none;
}

.f-row .fv {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-title);
  text-align: right;
  max-width: 65%;
  word-break: break-all;
}

.f-row .fv.seat {
  font-size: 19px;
  font-weight: 800;
  color: var(--green-strong);
  letter-spacing: 1px;
}

/* 已签到状态区 */
.zone {
  margin-top: 26px;
  text-align: center;
  padding: 0 28px;
  flex: none;
}

.done-ck {
  width: 52px;
  height: 52px;
  margin: 0 auto 14px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--green-mid-2), var(--green-strong));
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 22px -8px rgba(10, 85, 60, 0.5);
}

.done-ck svg {
  width: 26px;
  height: 26px;
  stroke: #fff;
  stroke-width: 3;
}

.zone .st {
  font-size: 19px;
  font-weight: 700;
  color: var(--green-strong);
  letter-spacing: 2px;
}

.zone .tm {
  font-size: 12.5px;
  color: var(--text-soft);
  margin-top: 7px;
}

/* 未签到二维码区 */
.qr-zone {
  margin-top: 2px;
  text-align: center;
  padding: 0 28px 32px;
  flex: none;
}

.qr-zone .pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--pill-text);
  background: var(--pill-bg);
  border: 1px solid var(--pill-border);
  padding: 5px 13px;
  border-radius: 999px;
}

.qr-zone .qr-box {
  margin: 14px auto 0;
  width: 240px;
  height: 240px;
  padding: 12px;
  border-radius: 18px;
  border: 1.5px dashed var(--frame-border);
  background: var(--frame-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.qr-zone .qr-box :deep(.guest-qr-code) {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr-zone .qr-box :deep(.guest-qr-code__frame) {
  width: 100%;
  height: 100%;
  border: none;
  padding: 0;
  background: transparent;
}

.qr-zone .qr-box :deep(.guest-qr-code__image) {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain;
}

.qr-zone .tip {
  margin-top: 15px;
  font-size: 13px;
  color: #5b7266;
}

.qr-zone .tip b {
  color: var(--green-strong);
}

/* 小屏：边缘缩小留白 */
@media (max-width: 360px) {
  .fields {
    margin-left: 20px;
    margin-right: 20px;
  }

  .who__name {
    font-size: 24px;
  }

  .qr-zone,
  .zone {
    padding-left: 18px;
    padding-right: 18px;
  }
}

/* PC 端：以手机宽度居中展示，更大屏可被遮挡，让嘉宾视角仍然聚焦 */
@media (min-width: 768px) {
  .guest-home-page {
    align-items: center;
  }

  .guest-home-shell {
    min-height: 100vh;
    box-shadow:
      0 24px 64px -12px rgba(20, 50, 35, 0.22),
      0 4px 16px rgba(20, 50, 35, 0.08);
  }
}
</style>