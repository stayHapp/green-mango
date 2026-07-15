<template>
  <section class="page staff-check-in-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">工作人员端</p>
        <h1>{{ meeting?.title ?? '会议签到' }}</h1>
        <dl v-if="meeting" class="compact-info-list">
          <dt>时间</dt>
          <dd>{{ formatDate(meeting.startTime) }} - {{ formatDate(meeting.endTime) }}</dd>
          <dt>地点</dt>
          <dd>{{ meeting.location }}</dd>
        </dl>
        <p v-else class="muted">请先选择会议。</p>
      </div>
      <div class="heading-actions">
        <el-button v-if="!session.staff" type="primary" @click="goLogin">去登录</el-button>
      </div>
    </div>

    <el-empty v-if="!session.staff" description="暂无工作人员会话" />
    <el-empty v-else-if="!meeting" description="未找到会议" />
    <div v-else class="guest-content-stack">
      <el-alert
        v-if="!isOnline"
        type="error"
        :closable="false"
        title="网络连接已断开，暂时无法完成新的签到操作；请恢复网络后重试。"
      />
      <div class="stats-grid staff-stats-grid">
        <el-card shadow="never"><div class="stat-number">{{ guests.length }}</div><div class="muted">参会人员</div></el-card>
        <el-card shadow="never"><div class="stat-number">{{ checkedCount }}</div><div class="muted">已签到</div></el-card>
        <el-card shadow="never"><div class="stat-number">{{ uncheckedCount }}</div><div class="muted">未签到</div></el-card>
      </div>

      <div class="detail-grid staff-detail-grid">
        <el-card shadow="never" class="form-card">
          <template #header>扫码签到</template>
          <el-form label-position="top" @submit.prevent>
            <el-form-item label="嘉宾二维码 token">
              <el-input v-model="qrToken" placeholder="请输入或粘贴嘉宾 token" />
            </el-form-item>
            <div class="action-row">
              <el-button :disabled="!isOnline" @click="startCameraScan">手机扫码</el-button>
              <el-button @click="fillDemoToken">填入示例</el-button>
              <el-button type="primary" :loading="loading" :disabled="!isOnline" @click="handleScan">确认签到</el-button>
            </div>
          </el-form>
          <div v-if="cameraScanning" id="staff-qr-reader" class="camera-preview" />
          <el-button v-if="cameraScanning" class="top-gap" @click="stopCameraScan">停止扫码</el-button>
        </el-card>

        <el-card shadow="never">
          <template #header>签到结果</template>
          <el-empty v-if="!scanResult" description="等待签到" />
          <div v-else>
            <el-alert :type="resultAlertType" :closable="false" :title="scanResult.message" />
            <dl v-if="scanResult.guest" class="info-list top-gap">
              <dt>嘉宾</dt>
              <dd>{{ scanResult.guest.name }}</dd>
              <dt>电话</dt>
              <dd>{{ scanResult.guest.phone }}</dd>
              <dt>座位</dt>
              <dd>{{ scanResult.guest.seat }}</dd>
            </dl>
          </div>
        </el-card>
      </div>

      <el-tabs model-value="guests" class="section-tabs">
        <el-tab-pane label="参会人员" name="guests">
          <el-input v-model="guestQuery" clearable class="table-search" placeholder="搜索姓名、手机号、单位或座位号，核验嘉宾签到状态" />
          <el-table class="staff-desktop-table" :data="filteredGuestRows" row-key="id">
            <el-table-column prop="name" label="姓名" width="120" />
            <el-table-column label="电话" min-width="150">
              <template #default="{ row }">
                <a v-if="!row.checkedIn" class="phone-link" :href="`tel:${row.phone}`">{{ row.phone }}</a>
                <span v-else>{{ row.phone }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="tag" label="身份" width="120" />
            <el-table-column prop="seat" label="座位" width="100" />
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="row.checkedIn ? 'success' : 'info'">{{ row.checkedIn ? '已签到' : '未签到' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button v-if="!row.checkedIn" type="primary" size="small" :loading="manualLoadingId === row.id" :disabled="!isOnline" @click="handleManualCheckIn(row.id)">标记签到</el-button>
                <span v-else class="muted">已完成</span>
              </template>
            </el-table-column>
          </el-table>
          <div class="staff-mobile-list">
            <el-empty v-if="!filteredGuestRows.length" description="未找到匹配嘉宾" :image-size="72" />
            <article v-for="row in filteredGuestRows" :key="row.id" class="staff-mobile-card">
              <div class="staff-mobile-card__header">
                <div>
                  <strong>{{ row.name }}</strong>
                  <p>{{ row.organization }}</p>
                </div>
                <el-tag :type="row.checkedIn ? 'success' : 'info'">{{ row.checkedIn ? '已签到' : '未签到' }}</el-tag>
              </div>
              <div class="staff-mobile-card__meta">
                <span>{{ row.tag }}</span>
                <span>座位 {{ row.seat }}</span>
              </div>
              <a v-if="!row.checkedIn" class="phone-link staff-mobile-card__phone" :href="`tel:${row.phone}`">{{ row.phone }}</a>
              <span v-else class="staff-mobile-card__phone">{{ row.phone }}</span>
              <el-button
                v-if="!row.checkedIn"
                class="staff-mobile-card__action"
                type="primary"
                :loading="manualLoadingId === row.id"
                :disabled="!isOnline"
                @click="handleManualCheckIn(row.id)"
              >
                确认签到
              </el-button>
            </article>
          </div>
        </el-tab-pane>
        <el-tab-pane label="签到列表" name="checkins">
          <el-table class="staff-desktop-table" :data="checkInRows" row-key="id">
            <el-table-column prop="guestName" label="姓名" width="120" />
            <el-table-column prop="phone" label="电话" min-width="150" />
            <el-table-column label="签到时间" min-width="180">
              <template #default="{ row }">{{ formatDate(row.checkedInAt) }}</template>
            </el-table-column>
            <el-table-column label="方式" width="110">
              <template #default="{ row }">{{ methodText(row.method) }}</template>
            </el-table-column>
          </el-table>
          <div class="staff-mobile-list">
            <el-empty v-if="!checkInRows.length" description="暂无签到记录" :image-size="72" />
            <article v-for="row in checkInRows" :key="row.id" class="staff-mobile-card staff-mobile-check-in-card">
              <div class="staff-mobile-card__header">
                <strong>{{ row.guestName }}</strong>
                <el-tag type="success">{{ methodText(row.method) }}</el-tag>
              </div>
              <span class="staff-mobile-card__phone">{{ row.phone }}</span>
              <p class="staff-mobile-card__time">{{ formatDate(row.checkedInAt) }}</p>
            </article>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Html5Qrcode } from 'html5-qrcode'

import { getMeeting, listCheckIns, listGuests, markGuestCheckedIn, scanGuest } from '../../mock/mockApi'
import { useSessionStore } from '../../stores/session'
import type { CheckInRecord, Guest, Meeting, ScanResult } from '../../types'

interface GuestRow extends Guest {
  checkedIn: boolean
}

interface CheckInRow extends CheckInRecord {
  guestName: string
  phone: string
}

interface BarcodeDetectorLike { detect(source: CanvasImageSource): Promise<Array<{ rawValue: string }>> }

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const guests = ref<Guest[]>([])
const checkIns = ref<CheckInRecord[]>([])
const qrToken = ref('')
const guestQuery = ref('')
const loading = ref(false)
const manualLoadingId = ref('')
const isOnline = ref(navigator.onLine)
const cameraScanning = ref(false)
let qrScanner: Html5Qrcode | undefined
const scanResult = ref<ScanResult>()
const resultAlertType = computed(alertType)
const checkedCount = computed(() => checkIns.value.length)
const uncheckedCount = computed(() => Math.max(guests.value.length - checkedCount.value, 0))
const guestRows = computed<GuestRow[]>(() => guests.value.map((guest) => ({
  ...guest,
  checkedIn: checkIns.value.some((record) => record.guestId === guest.id),
})))
const filteredGuestRows = computed<GuestRow[]>(filterGuestRows)
const checkInRows = computed<CheckInRow[]>(() => checkIns.value.map((record) => {
  const guest = guests.value.find((item) => item.id === record.guestId)
  return {
    ...record,
    guestName: guest?.name ?? '未知嘉宾',
    phone: guest?.phone ?? '-',
  }
}))

/**
 * 按工作人员输入的关键信息筛选嘉宾，用于现场身份与签到状态核验。
 *
 * 入参：
 *   无；函数读取当前搜索关键词和已加载的嘉宾行。
 *
 * 返回值：
 *   GuestRow[]：匹配姓名、手机号、单位或座位号的嘉宾行；空关键词时返回全部嘉宾。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function filterGuestRows(): GuestRow[] {
  const keyword = guestQuery.value.trim().toLocaleLowerCase('zh-CN')

  // 未输入关键词时保留完整名单，方便工作人员直接核验与签到。
  if (!keyword) {
    return guestRows.value
  }

  return guestRows.value.filter((guest) => [guest.name, guest.phone, guest.organization, guest.seat]
    .some((value) => value.toLocaleLowerCase('zh-CN').includes(keyword)))
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
  try {
    cameraScanning.value = true
    await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
    qrScanner = new Html5Qrcode('staff-qr-reader')
    await qrScanner.start({ facingMode: 'environment' }, { fps: 10, qrbox: { width: 240, height: 240 } }, async (decodedText) => { qrToken.value = decodedText; await stopCameraScan(); await handleScan() }, () => undefined)
  } catch { stopCameraScan(); ElMessage.error('无法打开摄像头，请检查权限后重试。') }
}

/**
 * 停止摄像头扫码并释放媒体设备资源。
 *
 * 入参：无。
 * 返回值：void：关闭视频轨道和扫描循环。
 * 异常：当前函数不主动抛出异常。
 */
async function stopCameraScan(): Promise<void> {
  if (qrScanner?.isScanning) await qrScanner.stop()
  qrScanner = undefined
  cameraScanning.value = false
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
 * 异常：
 *   当前 mock API 不主动抛出异常；会议不存在时页面展示空状态。
 */
async function loadDetail(): Promise<void> {
  const meetingId = String(route.params.id)
  const [meetingData, guestData, checkInData] = await Promise.all([
    getMeeting(meetingId),
    listGuests(meetingId),
    listCheckIns(meetingId),
  ])
  meeting.value = meetingData
  guests.value = guestData
  checkIns.value = checkInData
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
 *   当前 mock API 不主动抛出异常。
 */
async function refreshCheckIns(): Promise<void> {
  checkIns.value = await listCheckIns(String(route.params.id))
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
 * 填入 mock 数据中的嘉宾二维码 token 示例。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：只更新当前 token 输入框。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function fillDemoToken(): void {
  qrToken.value = 'QR-MEDU-G002'
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
 * 异常：
 *   当前 mock API 不主动抛出异常；缺少工作人员会话或 token 时展示错误结果。
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
  scanResult.value = await scanGuest(String(route.params.id), session.staff.id, qrToken.value.trim())
  loading.value = false
  await refreshCheckIns()
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
 * 异常：
 *   当前 mock API 不主动抛出异常；缺少工作人员会话时展示错误结果。
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
  scanResult.value = await markGuestCheckedIn(String(route.params.id), session.staff.id, guestId)
  manualLoadingId.value = ''
  await refreshCheckIns()
}

/**
 * 跳转到管理与签到登录页。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：只触发前端路由跳转。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function goLogin(): void {
  router.push('/login')
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
onUnmounted(stopNetworkMonitoring)
onUnmounted(() => { void stopCameraScan() })
</script>
