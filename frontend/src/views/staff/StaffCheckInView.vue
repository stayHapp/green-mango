<template>
  <section class="staff-workspace-page">
    <header class="staff-workspace-header">
      <div>
        <h1>{{ activeModeTitle }}</h1>
        <p>{{ session.staff?.name || '工作人员' }}</p>
      </div>
      <button type="button" class="staff-workspace-logout" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon>
        退出
      </button>
    </header>

    <main class="staff-workspace-content">
      <el-empty v-if="!session.staff" description="请先登录当前会议工作人员端">
        <el-button type="primary" @click="goLogin">前往登录</el-button>
      </el-empty>
      <el-alert v-else-if="pageError" type="error" :closable="false" :title="pageError" />
      <el-skeleton v-else-if="pageLoading" :rows="8" animated />
      <el-empty v-else-if="!meeting" description="未找到会议" />

      <template v-else>
        <el-alert
          v-if="!isOnline"
          class="staff-network-alert"
          type="error"
          :closable="false"
          title="网络连接已断开，暂时无法完成新的签到操作；请恢复网络后重试。"
        />

        <section class="staff-current-meeting" aria-labelledby="staff-current-meeting-title">
          <span>当前会议</span>
          <h2 id="staff-current-meeting-title">{{ meeting.title }}</h2>
        </section>

        <section v-if="activeMode === 'scan'" class="staff-scan-view">
          <div class="staff-scan-stage" :class="{ 'is-scanning': cameraScanning }">
            <div id="staff-qr-reader" class="staff-scan-camera" />
            <div v-if="!cameraScanning" class="staff-scan-placeholder">
              <el-icon><Camera /></el-icon>
              <span>开启摄像头扫描嘉宾二维码</span>
            </div>
            <i class="staff-scan-corner is-top-left" />
            <i class="staff-scan-corner is-top-right" />
            <i class="staff-scan-corner is-bottom-left" />
            <i class="staff-scan-corner is-bottom-right" />
            <i v-if="cameraScanning" class="staff-scan-line" />
          </div>

          <p class="staff-scan-guide">将嘉宾出示的二维码对准扫描框</p>
          <el-button
            v-if="!cameraScanning"
            class="staff-camera-button"
            type="primary"
            :loading="cameraStarting"
            :disabled="!isOnline"
            @click="startCameraScan"
          >
            开启摄像头
          </el-button>
          <el-button
            v-else
            class="staff-camera-button"
            plain
            :disabled="cameraStarting"
            @click="stopCameraScan"
          >
            关闭摄像头
          </el-button>
          <button type="button" class="staff-manual-link" @click="switchWorkspaceMode('manual')">
            无法扫码？手动签到
          </button>

          <section v-if="scanResult" class="staff-scan-result" aria-live="polite">
            <el-alert :type="resultAlertType" :closable="false" :title="scanResult.message" />
            <dl v-if="scanResult.guest">
              <div><dt>嘉宾</dt><dd>{{ scanResult.guest.name }}</dd></div>
              <div><dt>电话</dt><dd>{{ scanResult.guest.phone }}</dd></div>
              <div><dt>座位</dt><dd>{{ scanResult.guest.seat || '待分配' }}</dd></div>
            </dl>
          </section>
        </section>

        <section v-else-if="activeMode === 'manual'" class="staff-manual-view">
          <template v-if="selectedManualGuest">
            <article class="staff-confirm-card">
              <div class="staff-confirm-card__identity">
                <span>{{ selectedManualGuest.name.slice(0, 1) }}</span>
                <div>
                  <h2>{{ selectedManualGuest.name }}</h2>
                  <p>{{ selectedManualGuest.phone }}</p>
                  <el-tag :type="selectedManualGuest.checkedIn ? 'success' : 'info'">
                    {{ selectedManualGuest.checkedIn ? '已签到' : '待签到' }}
                  </el-tag>
                </div>
              </div>
              <dl class="staff-confirm-card__details">
                <div><dt>单位</dt><dd>{{ selectedManualGuest.organization || '未填写' }}</dd></div>
                <div><dt>身份</dt><dd>{{ selectedManualGuest.tag || '嘉宾' }}</dd></div>
                <div><dt>座位</dt><dd>{{ selectedManualGuest.seat || '待分配' }}</dd></div>
              </dl>
            </article>
            <div class="staff-confirm-tip">
              <el-icon><InfoFilled /></el-icon>
              请核对嘉宾信息后确认签到
            </div>
            <div class="staff-confirm-actions">
              <el-button @click="clearManualSelection">下一位</el-button>
              <el-button
                type="primary"
                :loading="manualLoadingId === selectedManualGuest.id"
                :disabled="!isOnline || selectedManualGuest.checkedIn"
                @click="confirmManualCheckIn"
              >
                {{ selectedManualGuest.checkedIn ? '已签到' : '确认签到' }}
              </el-button>
            </div>
          </template>

          <template v-else>
            <el-input
              v-model="guestQuery"
              clearable
              class="staff-guest-search"
              placeholder="搜索姓名、手机号、单位或座位号"
              :prefix-icon="Search"
            />
            <div class="staff-manual-results">
              <el-empty v-if="!filteredGuestRows.length" description="未找到匹配嘉宾" :image-size="72" />
              <article v-for="row in filteredGuestRows" :key="row.id" class="staff-guest-row">
                <span class="staff-guest-row__avatar">{{ row.name.slice(0, 1) }}</span>
                <div class="staff-guest-row__copy">
                  <strong>{{ row.name }}</strong>
                  <p>{{ row.phone }}</p>
                  <small>{{ row.organization || row.tag }} · 座位 {{ row.seat || '待分配' }}</small>
                </div>
                <el-button
                  v-if="!row.checkedIn"
                  type="primary"
                  plain
                  @click="selectManualGuest(row)"
                >
                  核对签到
                </el-button>
                <el-tag v-else type="success">已签到</el-tag>
              </article>
            </div>
          </template>
        </section>

        <section v-else class="staff-records-view">
          <div class="staff-workspace-stats" aria-label="签到统计">
            <div><strong>{{ guests.length }}</strong><span>参会人员</span></div>
            <div><strong>{{ checkedCount }}</strong><span>已签到</span></div>
            <div><strong>{{ uncheckedCount }}</strong><span>未签到</span></div>
          </div>
          <el-empty v-if="!checkInRows.length" description="暂无签到记录" :image-size="72" />
          <article v-for="row in checkInRows" :key="row.id" class="staff-record-row">
            <span>{{ row.guestName.slice(0, 1) }}</span>
            <div>
              <strong>{{ row.guestName }}</strong>
              <p>{{ row.phone }}</p>
              <small>{{ formatDate(row.checkedInAt) }}</small>
            </div>
            <em>{{ methodText(row.method) }}</em>
          </article>
        </section>
      </template>
    </main>

    <nav v-if="session.staff && meeting" class="staff-workspace-nav" aria-label="签到工作台导航">
      <button
        v-for="item in workspaceModes"
        :key="item.key"
        type="button"
        :class="{ 'is-active': activeMode === item.key }"
        @click="switchWorkspaceMode(item.key)"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </button>
    </nav>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Camera, InfoFilled, Postcard, Search, SwitchButton, Tickets } from '@element-plus/icons-vue'
import { Html5Qrcode } from 'html5-qrcode'

import { getApiErrorMessage } from '../../api/client'
import { logoutClientSession } from '../../api/sessions'
import {
  listStaffCheckIns,
  listStaffMeetings,
  manualStaffCheckIn,
  scanStaffCheckIn,
  searchStaffGuests,
  type StaffGuest,
} from '../../api/staffCheckIns'
import { useSessionStore } from '../../stores/session'
import type { CheckInRecord, Meeting, ScanResult } from '../../types'

interface CheckInRow extends CheckInRecord {
  guestName: string
  phone: string
}

interface BarcodeDetectorLike { detect(source: CanvasImageSource): Promise<Array<{ rawValue: string }>> }

type StaffWorkspaceMode = 'scan' | 'manual' | 'records'

interface StaffWorkspaceModeItem {
  key: StaffWorkspaceMode
  label: string
  icon: Component
}

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const guests = ref<StaffGuest[]>([])
const displayedGuests = ref<StaffGuest[]>([])
const checkIns = ref<CheckInRecord[]>([])
const qrToken = ref('')
const guestQuery = ref('')
const loading = ref(false)
const manualLoadingId = ref('')
const isOnline = ref(navigator.onLine)
const cameraScanning = ref(false)
const cameraStarting = ref(false)
const pageLoading = ref(false)
const pageError = ref('')
const activeMode = ref<StaffWorkspaceMode>('scan')
const selectedManualGuest = ref<StaffGuest>()
let guestSearchTimer: number | undefined
let qrScanner: Html5Qrcode | undefined
let cameraScanGeneration = 0
const scanResult = ref<ScanResult>()
const resultAlertType = computed(alertType)
const activeModeTitle = computed(currentModeTitle)
const checkedCount = computed(() => checkIns.value.length)
const uncheckedCount = computed(() => Math.max(guests.value.length - checkedCount.value, 0))
const filteredGuestRows = computed(() => displayedGuests.value)
const checkInRows = computed<CheckInRow[]>(() => checkIns.value.map((record) => {
  const guest = guests.value.find((item) => item.id === record.guestId)
  return {
    ...record,
    guestName: guest?.name ?? '未知嘉宾',
    phone: guest?.phone ?? '-',
  }
}))
const workspaceModes: StaffWorkspaceModeItem[] = [
  { key: 'scan', label: '扫码签到', icon: Camera },
  { key: 'manual', label: '手动签到', icon: Postcard },
  { key: 'records', label: '签到记录', icon: Tickets },
]

/**
 * 根据当前工作台模式返回页面标题。
 *
 * 入参：无；函数读取 activeMode 当前值。
 * 返回值：string：扫码签到、手动签到或签到记录标题。
 * 异常：当前函数不主动抛出异常。
 */
function currentModeTitle(): string {
  const titleMap: Record<StaffWorkspaceMode, string> = {
    scan: '扫码签到',
    manual: selectedManualGuest.value ? '确认嘉宾' : '手动签到',
    records: '签到记录',
  }
  return titleMap[activeMode.value]
}

/**
 * 切换工作人员签到工作台模式，并在离开扫码页时释放摄像头。
 *
 * 入参：mode 为目标模式，必填，可取 scan、manual 或 records。
 * 返回值：Promise<void>：完成必要资源清理后更新当前模式。
 * 异常：摄像头清理异常由 stopCameraScan 内部吸收。
 */
async function switchWorkspaceMode(mode: StaffWorkspaceMode): Promise<void> {
  if (activeMode.value === 'scan' && mode !== 'scan') {
    await stopCameraScan()
  }
  activeMode.value = mode
  if (mode !== 'manual') {
    selectedManualGuest.value = undefined
  }
}

/**
 * 选择手动签到搜索结果，进入嘉宾资料核对状态。
 *
 * 入参：guest 为需要核对的嘉宾，必填。
 * 返回值：void：保存选中嘉宾并更新页面标题。
 * 异常：当前函数不主动抛出异常。
 */
function selectManualGuest(guest: StaffGuest): void {
  selectedManualGuest.value = guest
}

/**
 * 清除当前手动签到嘉宾，返回搜索结果列表。
 *
 * 入参：无。
 * 返回值：void：清空当前选中嘉宾。
 * 异常：当前函数不主动抛出异常。
 */
function clearManualSelection(): void {
  selectedManualGuest.value = undefined
}

/**
 * 对核对后的当前嘉宾执行人工签到。
 *
 * 入参：无；函数读取 selectedManualGuest 当前值。
 * 返回值：Promise<void>：签到成功后刷新数据、提示结果并返回搜索列表。
 * 异常：没有选中嘉宾时直接结束；业务异常由 handleManualCheckIn 转换为签到结果。
 */
async function confirmManualCheckIn(): Promise<void> {
  if (!selectedManualGuest.value) {
    return
  }
  await handleManualCheckIn(selectedManualGuest.value.id)
  if (scanResult.value?.status === 'success') {
    ElMessage.success('人工签到成功。')
    selectedManualGuest.value = undefined
  } else if (scanResult.value?.message) {
    ElMessage.warning(scanResult.value.message)
  }
}

/**
 * 退出工作人员会话并返回当前会议专属登录入口。
 *
 * 入参：无；函数读取当前路由会议 ID 和工作人员会话。
 * 返回值：Promise<void>：无论服务端撤销是否成功，均清理本地会话并完成路由跳转。
 * 异常：服务端撤销失败时显示警告但不向外抛出。
 */
async function handleLogout(): Promise<void> {
  const meetingId = String(route.params.id)
  try {
    await logoutClientSession('staff')
  } catch {
    ElMessage.warning('服务端会话可能已失效，本地登录状态已清除。')
  } finally {
    await stopCameraScan()
    session.clearStaff()
    await router.replace(`/meetings/${meetingId}/staff/login`)
  }
}

/**
 * 延迟触发服务端嘉宾搜索，避免连续输入产生过多请求。
 *
 * 入参：无；函数读取当前搜索关键词。
 * 返回值：void：重置 300 毫秒搜索计时器。
 * 异常：搜索接口异常由 loadGuests 转换为页面消息。
 */
function scheduleGuestSearch(): void {
  if (guestSearchTimer !== undefined) {
    window.clearTimeout(guestSearchTimer)
  }
  guestSearchTimer = window.setTimeout(() => { void loadGuests(guestQuery.value) }, 300)
}

/**
 * 同步浏览器当前网络连接状态。
 *
 * 入参：
 *   无；函数读取浏览器 Navigator（导航器）对象的在线状态。
 *
 * 返回值：
 *   void：更新页面网络状态提示和签到按钮可用状态。
 *
 * 异常：
 *   当前函数不主动抛出异常；浏览器不支持网络状态检测时按其默认在线状态处理。
 */
function updateNetworkStatus(): void {
  isOnline.value = navigator.onLine
}

/**
 * 启动工作人员签到页的网络状态监听。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：注册网络连接和断开事件监听，并立即同步一次状态。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function startNetworkMonitoring(): void {
  updateNetworkStatus()
  window.addEventListener('online', updateNetworkStatus)
  window.addEventListener('offline', updateNetworkStatus)
}

/**
 * 停止工作人员签到页的网络状态监听，避免离开页面后残留事件处理器。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：移除网络连接和断开事件监听。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function stopNetworkMonitoring(): void {
  window.removeEventListener('online', updateNetworkStatus)
  window.removeEventListener('offline', updateNetworkStatus)
}

/**
 * 启动手机后置摄像头并识别嘉宾二维码。
 *
 * 入参：无。
 * 返回值：Promise<void>：成功识别后自动填充 token 并执行签到。
 * 异常：摄像头权限被拒绝或浏览器不支持扫码能力时展示提示。
 */
async function startCameraScan(): Promise<void> {
  if (cameraScanning.value) {
    return
  }

  const scanGeneration = ++cameraScanGeneration
  try {
    cameraStarting.value = true
    cameraScanning.value = true
    await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
    if (scanGeneration !== cameraScanGeneration) {
      return
    }

    const scanner = new Html5Qrcode('staff-qr-reader')
    qrScanner = scanner
    await scanner.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: { width: 240, height: 240 } },
      (decodedText) => { void handleCameraDecoded(decodedText, scanGeneration) },
      ignoreCameraDecodeError,
    )
    if (scanGeneration !== cameraScanGeneration) {
      await releaseQrScanner(scanner)
      return
    }
    cameraStarting.value = false
  } catch {
    if (scanGeneration === cameraScanGeneration) {
      await stopCameraScan()
      ElMessage.error('无法打开摄像头，请检查权限后重试。')
    }
  }
}

/**
 * 处理摄像头成功识别出的嘉宾二维码。
 *
 * 入参：decodedText 为二维码文本；scanGeneration 为启动本轮扫码时的代次编号，均必填。
 * 返回值：Promise<void>：当前扫码仍有效时关闭摄像头并提交签到。
 * 异常：签到业务异常由 handleScan 转换为页面结果；过期扫码回调会被忽略。
 */
async function handleCameraDecoded(decodedText: string, scanGeneration: number): Promise<void> {
  if (scanGeneration !== cameraScanGeneration) {
    return
  }
  qrToken.value = decodedText
  await stopCameraScan()
  await handleScan()
}

/**
 * 忽略单帧未识别二维码的错误，让摄像头继续扫描后续画面。
 *
 * 入参：无；二维码库可能传入错误文本，但当前流程不需要使用。
 * 返回值：void：不修改页面状态。
 * 异常：当前函数不主动抛出异常。
 */
function ignoreCameraDecodeError(): void {
  // 单帧没有识别到二维码属于正常扫描过程，不向工作人员展示错误。
}

/**
 * 停止并清理一个二维码扫描器实例，释放摄像头媒体轨道和页面资源。
 *
 * 入参：scanner 为需要释放的 Html5Qrcode 实例，必填。
 * 返回值：Promise<void>：无论库方法是否报错，最终都会尝试清理实例。
 * 异常：停止或清理异常会在函数内部吸收，避免关闭操作阻断页面离开。
 */
async function releaseQrScanner(scanner: Html5Qrcode): Promise<void> {
  try {
    if (scanner.isScanning) {
      await scanner.stop()
    }
  } catch {
    // 浏览器可能在媒体轨道已结束时再次抛错，此时继续执行资源清理。
  }
  try {
    scanner.clear()
  } catch {
    // 扫描容器已卸载时清理可能失败，不影响摄像头关闭结果。
  }
}

/**
 * 停止摄像头扫码并释放媒体设备资源。
 *
 * 入参：无。
 * 返回值：Promise<void>：立即退出扫码界面，并停止视频轨道和扫描循环。
 * 异常：二维码库停止或清理异常由 releaseQrScanner 吸收。
 */
async function stopCameraScan(): Promise<void> {
  cameraScanGeneration += 1
  const scanner = qrScanner
  qrScanner = undefined
  cameraStarting.value = false
  cameraScanning.value = false
  if (scanner) {
    await releaseQrScanner(scanner)
  }
}

/**
 * 加载工作人员签到工作台所需数据。
 *
 * 入参：
 *   无；函数从当前路由参数读取会议 ID。
 *
 * 返回值：
 *   Promise<void>：加载完成后更新会议、参会人员和签到列表。
 *
 * 异常：登录过期、会议未授权或网络异常时展示页面错误。
 */
async function loadDetail(): Promise<void> {
  const meetingId = String(route.params.id)
  pageLoading.value = true
  pageError.value = ''
  try {
    const [meetingData, guestData, checkInData] = await Promise.all([
      listStaffMeetings(),
      searchStaffGuests(meetingId, ''),
      listStaffCheckIns(meetingId),
    ])
    meeting.value = meetingData.find((item) => item.id === meetingId)
    if (!meeting.value) {
      throw new Error('会议不存在或无签到权限。')
    }
    guests.value = guestData
    displayedGuests.value = guestData
    checkIns.value = checkInData
  } catch (error) {
    meeting.value = undefined
    pageError.value = getApiErrorMessage(error, '签到工作台加载失败。')
  } finally {
    pageLoading.value = false
  }
}

/**
 * 调用服务端按关键词查询嘉宾。
 *
 * 入参：query 为姓名、手机号、单位或座位关键词，可为空。
 * 返回值：Promise<void>：成功后更新当前展示结果。
 * 异常：接口异常时保留原列表并展示消息提示。
 */
async function loadGuests(query: string): Promise<void> {
  try {
    displayedGuests.value = await searchStaffGuests(String(route.params.id), query.trim())
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '嘉宾搜索失败。'))
  }
}

/**
 * 重新加载签到记录。
 *
 * 入参：
 *   无；函数从当前路由参数读取会议 ID。
 *
 * 返回值：
 *   Promise<void>：加载完成后更新签到列表和参会人员状态。
 *
 * 异常：
 *   任一刷新接口失败时向调用方抛出异常，由签到操作流程展示错误提示。
 */
async function refreshCheckIns(): Promise<void> {
  const meetingId = String(route.params.id)
  const [guestData, displayedGuestData, checkInData] = await Promise.all([
    searchStaffGuests(meetingId, ''),
    searchStaffGuests(meetingId, guestQuery.value.trim()),
    listStaffCheckIns(meetingId),
  ])
  guests.value = guestData
  displayedGuests.value = displayedGuestData
  checkIns.value = checkInData
}

/**
 * 根据签到状态计算 Element Plus 提示类型。
 *
 * 入参：
 *   无；函数读取当前签到结果状态。
 *
 * 返回值：
 *   'success' | 'warning' | 'error' | 'info'：适用于 el-alert 的类型。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function alertType(): 'success' | 'warning' | 'error' | 'info' {
  if (!scanResult.value) {
    return 'info'
  }

  if (scanResult.value.status === 'success') {
    return 'success'
  }

  if (scanResult.value.status === 'already_checked_in') {
    return 'warning'
  }

  return 'error'
}

/**
 * 执行扫码签到。
 *
 * 入参：
 *   无；函数从路由读取会议 ID，从会话读取工作人员 ID，从表单读取二维码 token。
 *
 * 返回值：
 *   Promise<void>：签到完成后更新结果和签到列表。
 *
 * 异常：缺少会话或 token 时展示错误；后端业务和网络异常转换为签到结果。
 */
async function handleScan(): Promise<void> {
  if (!session.staff) {
    scanResult.value = { status: 'invalid', message: '请先完成工作人员登录。' }
    return
  }

  // 网络断开时不提交新的签到请求，避免工作人员误以为操作已成功。
  if (!isOnline.value) {
    scanResult.value = { status: 'invalid', message: '网络连接已断开，请恢复网络后重新签到。' }
    return
  }

  if (!qrToken.value.trim()) {
    scanResult.value = { status: 'invalid', message: '请填写嘉宾二维码 token。' }
    return
  }

  loading.value = true
  try {
    const record = await scanStaffCheckIn(String(route.params.id), qrToken.value.trim())
    await refreshCheckIns()
    const guest = guests.value.find((item) => item.id === record.guestId)
    scanResult.value = {
      status: 'success',
      message: '签到成功。',
      guest: guest ? { ...guest, meetingId: record.meetingId, qrToken: '' } : undefined,
      checkIn: record,
    }
  } catch (error) {
    const message = getApiErrorMessage(error, '扫码签到失败。')
    scanResult.value = { status: message.includes('已签到') ? 'already_checked_in' : 'invalid', message }
  } finally {
    loading.value = false
  }
}

/**
 * 手动标记嘉宾签到。
 *
 * 入参：
 *   guestId：嘉宾 ID，必填。
 *
 * 返回值：
 *   Promise<void>：手动签到完成后更新结果和签到列表。
 *
 * 异常：缺少工作人员会话时展示错误；后端业务和网络异常转换为签到结果。
 */
async function handleManualCheckIn(guestId: string): Promise<void> {
  if (!session.staff) {
    scanResult.value = { status: 'invalid', message: '请先完成工作人员登录。' }
    return
  }

  // 网络断开时不提交新的签到请求，避免产生无法确认的现场状态。
  if (!isOnline.value) {
    scanResult.value = { status: 'invalid', message: '网络连接已断开，请恢复网络后重新签到。' }
    return
  }

  manualLoadingId.value = guestId
  try {
    const record = await manualStaffCheckIn(String(route.params.id), guestId)
    await refreshCheckIns()
    const guest = guests.value.find((item) => item.id === record.guestId)
    scanResult.value = {
      status: 'success',
      message: '人工签到成功。',
      guest: guest ? { ...guest, meetingId: record.meetingId, qrToken: '' } : undefined,
      checkIn: record,
    }
  } catch (error) {
    const message = getApiErrorMessage(error, '人工签到失败。')
    scanResult.value = { status: message.includes('已签到') ? 'already_checked_in' : 'invalid', message }
  } finally {
    manualLoadingId.value = ''
  }
}

/**
 * 跳转到当前会议专属工作人员登录页。
 *
 * 入参：
 *   无。
 *
 * 返回值：Promise<void>：完成当前会议工作人员登录页跳转。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
async function goLogin(): Promise<void> {
  await router.push(`/meetings/${String(route.params.id)}/staff/login`)
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
  return new Date(value).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}

/**
 * 将签到方式转换为中文文本。
 *
 * 入参：
 *   method：签到方式，必填，可取 scan 或 manual。
 *
 * 返回值：
 *   string：中文签到方式文本。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function methodText(method: CheckInRecord['method']): string {
  const map: Record<CheckInRecord['method'], string> = {
    scan: '扫码',
    manual: '手动',
  }
  return map[method]
}

onMounted(loadDetail)
onMounted(startNetworkMonitoring)
watch(guestQuery, scheduleGuestSearch)
onUnmounted(stopNetworkMonitoring)
onUnmounted(() => {
  if (guestSearchTimer !== undefined) window.clearTimeout(guestSearchTimer)
  void stopCameraScan()
})
</script>
