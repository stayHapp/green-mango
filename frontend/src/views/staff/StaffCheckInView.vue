<template>
  <section class="page">
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
        <el-button
          v-if="session.staff && meeting"
          type="primary"
          plain
          :icon="Download"
          :loading="exporting"
          @click="handleExportCheckInSheet"
        >
          导出签到表
        </el-button>
        <el-button v-if="!session.staff" type="primary" @click="goLogin">去登录</el-button>
      </div>
    </div>

    <el-empty v-if="!session.staff" description="暂无工作人员会话" />
    <el-empty v-else-if="!meeting" description="未找到会议" />
    <div v-else class="guest-content-stack">
      <div class="stats-grid">
        <el-card shadow="never"><div class="stat-number">{{ guests.length }}</div><div class="muted">参会人员</div></el-card>
        <el-card shadow="never"><div class="stat-number">{{ checkedCount }}</div><div class="muted">已签到</div></el-card>
        <el-card shadow="never"><div class="stat-number">{{ uncheckedCount }}</div><div class="muted">未签到</div></el-card>
      </div>

      <div class="detail-grid">
        <el-card shadow="never" class="form-card">
          <template #header>扫码签到</template>
          <el-form label-position="top" @submit.prevent>
            <el-form-item label="嘉宾二维码 token">
              <el-input v-model="qrToken" placeholder="请输入或粘贴嘉宾 token" />
            </el-form-item>
            <div class="action-row">
              <el-button @click="fillDemoToken">填入示例</el-button>
              <el-button type="primary" :loading="loading" @click="handleScan">确认签到</el-button>
            </div>
          </el-form>
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
          <el-table :data="guestRows" row-key="id">
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
                <el-button v-if="!row.checkedIn" type="primary" size="small" :loading="manualLoadingId === row.id" @click="handleManualCheckIn(row.id)">标记签到</el-button>
                <span v-else class="muted">已完成</span>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="签到列表" name="checkins">
          <el-table :data="checkInRows" row-key="id">
            <el-table-column prop="guestName" label="姓名" width="120" />
            <el-table-column prop="phone" label="电话" min-width="150" />
            <el-table-column label="签到时间" min-width="180">
              <template #default="{ row }">{{ formatDate(row.checkedInAt) }}</template>
            </el-table-column>
            <el-table-column label="方式" width="110">
              <template #default="{ row }">{{ methodText(row.method) }}</template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { utils, writeFileXLSX } from 'xlsx'

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

interface CheckInExportRow {
  序号: number
  姓名: string
  手机号: string
  单位: string
  职务: string
  身份: string
  座位号: string
  签到状态: string
  签到时间: string
  签到方式: string
}

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const guests = ref<Guest[]>([])
const checkIns = ref<CheckInRecord[]>([])
const qrToken = ref('')
const loading = ref(false)
const manualLoadingId = ref('')
const exporting = ref(false)
const scanResult = ref<ScanResult>()
const resultAlertType = computed(alertType)
const checkedCount = computed(() => checkIns.value.length)
const uncheckedCount = computed(() => Math.max(guests.value.length - checkedCount.value, 0))
const guestRows = computed<GuestRow[]>(() => guests.value.map((guest) => ({
  ...guest,
  checkedIn: checkIns.value.some((record) => record.guestId === guest.id),
})))
const checkInRows = computed<CheckInRow[]>(() => checkIns.value.map((record) => {
  const guest = guests.value.find((item) => item.id === record.guestId)
  return {
    ...record,
    guestName: guest?.name ?? '未知嘉宾',
    phone: guest?.phone ?? '-',
  }
}))

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

  manualLoadingId.value = guestId
  scanResult.value = await markGuestCheckedIn(String(route.params.id), session.staff.id, guestId)
  manualLoadingId.value = ''
  await refreshCheckIns()
}

/**
 * 将全量嘉宾和签到记录转换为导出工作表行。
 *
 * 入参：
 *   guestList：当前会议的嘉宾列表，必填。
 *   records：当前会议的签到记录，必填；每位嘉宾最多一条记录。
 *
 * 返回值：
 *   CheckInExportRow[]：按嘉宾列表顺序排列的签到表行，包含未签到嘉宾。
 *
 * 异常：
 *   当前函数不主动抛出异常；签到记录中找不到嘉宾时不会影响其他行。
 *
 * 示例：
 *   createCheckInExportRows(guests.value, checkIns.value)
 */
function createCheckInExportRows(guestList: Guest[], records: CheckInRecord[]): CheckInExportRow[] {
  const checkInByGuestId = new Map<string, CheckInRecord>()

  // 按嘉宾 ID 建立索引，便于在导出时快速关联签到信息。
  for (const record of records) {
    checkInByGuestId.set(record.guestId, record)
  }

  const rows: CheckInExportRow[] = []

  // 以嘉宾列表为基准，确保未签到嘉宾也会出现在导出的签到表中。
  for (const [index, guest] of guestList.entries()) {
    const record = checkInByGuestId.get(guest.id)
    rows.push({
      序号: index + 1,
      姓名: guest.name,
      手机号: guest.phone,
      单位: guest.organization,
      职务: guest.title,
      身份: guest.tag,
      座位号: guest.seat,
      签到状态: record ? '已签到' : '未签到',
      签到时间: record ? formatExportDate(record.checkedInAt) : '',
      签到方式: record ? methodText(record.method) : '',
    })
  }

  return rows
}

/**
 * 格式化 Excel 工作表中的签到时间。
 *
 * 入参：
 *   value：ISO 格式日期时间字符串，必填。
 *
 * 返回值：
 *   string：按中文地区习惯展示的本地日期时间。
 *
 * 异常：
 *   当前函数不主动抛出异常；非法日期将按浏览器默认结果展示。
 */
function formatExportDate(value: string): string {
  return new Date(value).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'medium', hour12: false })
}

/**
 * 生成符合文件系统命名规则的签到表文件名。
 *
 * 入参：
 *   currentMeeting：当前会议详情，必填。
 *
 * 返回值：
 *   string：由会议标题和“嘉宾签到表”组成的 xlsx 文件名。
 *
 * 异常：
 *   当前函数不主动抛出异常；标题中的文件系统保留字符会替换为下划线。
 */
function buildCheckInExportFileName(currentMeeting: Meeting): string {
  const safeTitle = currentMeeting.title.replace(/[\\/:*?"<>|]/g, '_')
  return `${safeTitle}-嘉宾签到表.xlsx`
}

/**
 * 导出当前会议的全量嘉宾签到表为 xlsx 文件。
 *
 * 入参：
 *   无；函数读取已加载的会议、嘉宾和签到记录。
 *
 * 返回值：
 *   Promise<void>：浏览器生成并下载 Excel 文件后结束。
 *
 * 异常：
 *   导出库写入文件失败时展示错误提示，不向页面外抛出异常。
 *
 * 示例：
 *   await handleExportCheckInSheet()
 */
async function handleExportCheckInSheet(): Promise<void> {
  if (!meeting.value) {
    ElMessage.warning('未找到会议，无法导出签到表。')
    return
  }

  exporting.value = true

  try {
    const worksheet = utils.json_to_sheet(createCheckInExportRows(guests.value, checkIns.value))
    worksheet['!cols'] = [
      { wch: 8 },
      { wch: 14 },
      { wch: 16 },
      { wch: 24 },
      { wch: 16 },
      { wch: 14 },
      { wch: 12 },
      { wch: 12 },
      { wch: 22 },
      { wch: 12 },
    ]
    const workbook = utils.book_new()
    utils.book_append_sheet(workbook, worksheet, '嘉宾签到表')
    writeFileXLSX(workbook, buildCheckInExportFileName(meeting.value))
    ElMessage.success('嘉宾签到表已开始下载。')
  } catch {
    ElMessage.error('签到表导出失败，请稍后重试。')
  } finally {
    exporting.value = false
  }
}

/**
 * 跳转到统一登录页。
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
</script>
