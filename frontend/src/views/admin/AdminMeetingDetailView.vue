<template>
  <section v-if="meeting" class="page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">管理员端</p>
        <h1>{{ meeting.title }}</h1>
        <p class="muted">{{ meeting.location }}｜{{ formatDate(meeting.startTime) }} - {{ formatDate(meeting.endTime) }}</p>
      </div>
      <div class="heading-actions">
        <el-button @click="goMeetings">返回会议管理</el-button>
        <el-button v-if="!session.admin" type="primary" @click="goLogin">去登录</el-button>
        <el-button
          v-else
          type="primary"
          plain
          :icon="Download"
          :loading="exporting"
          @click="handleExportCheckInSheet"
        >
          导出签到表
        </el-button>
        <el-tag type="success">签到 {{ checkedCount }}/{{ guests.length }}</el-tag>
      </div>
    </div>

    <el-alert v-if="!session.admin" class="top-gap" type="warning" :closable="false" title="请先完成管理员登录后再查看和编辑会议。" />

    <el-alert v-else-if="meeting.status === 'published'" class="top-gap" type="success" :closable="false" title="会议已发布，可将会议入口链接生成二维码后分享给嘉宾和工作人员。">
      <template #default>
        <p>会议 ID：{{ meeting.id }}</p>
        <div class="action-row"><el-input :model-value="meetingEntryUrl" readonly /><el-button type="primary" @click="copyMeetingEntryUrl">复制链接</el-button><el-button @click="openMeetingQrDialog">会议二维码</el-button></div>
        <el-dialog v-model="meetingQrDialogVisible" title="会议二维码" width="min(360px, calc(100% - 32px))" align-center>
          <img v-if="meetingQrCode" class="meeting-entry-qr" :src="meetingQrCode" alt="会议入口二维码" />
          <div class="action-row top-gap"><el-button type="primary" :disabled="!meetingQrCode" @click="downloadMeetingQrCode">下载二维码</el-button></div>
        </el-dialog>
      </template>
    </el-alert>

    <div v-else class="stats-grid">
      <el-card shadow="never"><div class="stat-number">{{ guests.length }}</div><div class="muted">嘉宾总数</div></el-card>
      <el-card shadow="never"><div class="stat-number">{{ checkedCount }}</div><div class="muted">已签到</div></el-card>
      <el-card shadow="never"><div class="stat-number">{{ staff.length }}</div><div class="muted">工作人员</div></el-card>
    </div>

    <el-tabs v-if="session.admin" model-value="guests" class="section-tabs">
      <el-tab-pane label="编辑会议" name="edit">
        <el-form class="edit-form" label-position="top" @submit.prevent>
          <div class="form-grid">
            <el-form-item label="会议名称">
              <el-input v-model="editForm.title" placeholder="请输入会议名称" />
            </el-form-item>
            <el-form-item label="会议状态">
              <el-select v-model="editForm.status" placeholder="请选择状态">
                <el-option label="草稿" value="draft" />
                <el-option label="已发布" value="published" />
                <el-option label="已结束" value="ended" />
              </el-select>
            </el-form-item>
          </div>
          <el-form-item label="会议地点">
            <el-input v-model="editForm.location" placeholder="请输入会议地点" />
          </el-form-item>
          <el-form-item label="会议说明">
            <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="请输入会议说明" />
          </el-form-item>
          <div class="form-grid">
            <el-form-item label="开始时间">
              <el-input v-model="editForm.startTime" type="datetime-local" />
            </el-form-item>
            <el-form-item label="结束时间">
              <el-input v-model="editForm.endTime" type="datetime-local" />
            </el-form-item>
          </div>
          <div class="action-row">
            <el-button @click="resetEditForm">重置</el-button>
            <el-button type="primary" :loading="saving" @click="saveMeeting">保存</el-button>
          </div>
          <el-alert v-if="saveMessage" class="top-gap" :type="saveMessageType" :closable="false" :title="saveMessage" />
        </el-form>
      </el-tab-pane>
      <el-tab-pane label="嘉宾" name="guests">
        <div class="action-row"><el-button @click="guestCreateDialogVisible = true">新增嘉宾</el-button><el-button type="primary" :loading="generatingGuestQr" @click="handleGenerateGuestQrTokens">一键生成嘉宾二维码</el-button></div>
        <el-alert v-if="guestQrMessage" class="top-gap" :type="guestQrMessageType" :closable="false" :title="guestQrMessage" />
        <el-table :data="guestRows" row-key="id">
          <el-table-column prop="name" label="姓名" width="120" />
          <el-table-column prop="organization" label="单位" min-width="180" />
          <el-table-column prop="title" label="职务" width="140" />
          <el-table-column prop="tag" label="标签" width="120" />
          <el-table-column prop="seat" label="座位" width="100" />
          <el-table-column label="签到" width="120">
            <template #default="{ row }">
              <el-tag :type="row.checkedIn ? 'success' : 'info'">{{ row.checkedIn ? '已签到' : '未签到' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100"><template #default="{ row }"><el-button size="small" @click="showGuestDetail(row)">查看</el-button></template></el-table-column>
        </el-table>
        <el-dialog v-model="guestCreateDialogVisible" title="新增嘉宾" width="min(520px, calc(100% - 32px))"><el-form label-position="top" @submit.prevent><div class="form-grid"><el-form-item label="姓名"><el-input v-model="guestForm.name" /></el-form-item><el-form-item label="手机号"><el-input v-model="guestForm.phone" /></el-form-item></div><div class="form-grid"><el-form-item label="单位"><el-input v-model="guestForm.organization" /></el-form-item><el-form-item label="职务"><el-input v-model="guestForm.title" /></el-form-item></div><div class="form-grid"><el-form-item label="身份"><el-input v-model="guestForm.tag" /></el-form-item><el-form-item label="座位"><el-input v-model="guestForm.seat" /></el-form-item></div><div class="action-row"><el-button type="primary" :loading="creatingGuest" @click="handleCreateGuest">保存嘉宾</el-button></div></el-form></el-dialog>
        <el-dialog v-model="guestDetailDialogVisible" title="嘉宾信息" width="min(420px, calc(100% - 32px))" align-center>
          <div v-loading="guestDetailLoading" class="guest-detail-content">
            <dl v-if="selectedGuest" class="info-list"><dt>姓名</dt><dd>{{ selectedGuest.name }}</dd><dt>手机号</dt><dd>{{ selectedGuest.phone }}</dd><dt>单位</dt><dd>{{ selectedGuest.organization }}</dd><dt>职务</dt><dd>{{ selectedGuest.title }}</dd><dt>身份</dt><dd>{{ selectedGuest.tag }}</dd><dt>座位</dt><dd>{{ selectedGuest.seat }}</dd></dl>
            <img v-if="guestQrCode" class="meeting-entry-qr" :src="guestQrCode" alt="嘉宾签到二维码" />
          </div>
        </el-dialog>
      </el-tab-pane>
      <el-tab-pane label="导入嘉宾" name="import">
        <el-alert type="info" :closable="false" title="第一版嘉宾固定使用姓名和手机号登录；导入文件首行需包含“姓名”和“手机号”列。" />
        <div class="action-row top-gap">
          <el-button @click="downloadGuestImportTemplate">下载 Excel 模板</el-button>
          <el-button type="primary" :loading="importing" @click="openGuestImportFilePicker">导入 Excel 名单</el-button>
          <input ref="guestImportInput" class="visually-hidden" type="file" accept=".xlsx" @change="handleGuestImportFileChange" />
        </div>
        <el-alert v-if="importMessage" class="top-gap" :type="importMessageType" :closable="false" :title="importMessage" />
      </el-tab-pane>
      <el-tab-pane label="字段" name="fields">
        <el-table :data="fields" row-key="id">
          <el-table-column prop="label" label="字段名称" />
          <el-table-column prop="key" label="字段标识" />
          <el-table-column label="嘉宾可见"><template #default="{ row }">{{ row.visibleToGuest ? '是' : '否' }}</template></el-table-column>
          <el-table-column label="登录验证"><template #default="{ row }">{{ row.usedForLogin ? '是' : '否' }}</template></el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="工作人员" name="staff">
        <el-form class="edit-form" label-position="top" @submit.prevent>
          <div class="form-grid">
            <el-form-item label="姓名"><el-input v-model="staffForm.name" placeholder="请输入姓名" /></el-form-item>
            <el-form-item label="手机号"><el-input v-model="staffForm.phone" placeholder="请输入手机号" /></el-form-item>
          </div>
          <el-form-item label="登录账号"><el-input v-model="staffForm.account" placeholder="请输入工作人员账号" /></el-form-item>
          <div class="action-row"><el-button type="primary" :loading="creatingStaff" @click="handleCreateStaff">创建并授权当前会议</el-button></div>
          <el-alert v-if="staffMessage" class="top-gap" :type="staffMessageType" :closable="false" :title="staffMessage" />
        </el-form>
        <el-table :data="staff" row-key="id">
          <el-table-column prop="name" label="姓名" />
          <el-table-column prop="account" label="账号" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="签到记录" name="checkins">
        <el-table :data="checkIns" row-key="id">
          <el-table-column label="嘉宾"><template #default="{ row }">{{ guestName(row.guestId) }}</template></el-table-column>
          <el-table-column label="工作人员"><template #default="{ row }">{{ staffName(row.staffId) }}</template></el-table-column>
          <el-table-column label="签到时间"><template #default="{ row }">{{ formatDate(row.checkedInAt) }}</template></el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </section>
  <section v-else class="page">
    <el-skeleton v-if="detailLoading" :rows="6" animated />
    <template v-else>
      <el-alert type="error" :closable="false" :title="detailError || '会议详情加载失败。'" />
      <div class="action-row top-gap"><el-button @click="goMeetings">返回会议管理</el-button></div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import QRCode from 'qrcode'

import { downloadAdminCheckInExport, downloadAdminGuestImportTemplate, importAdminGuests } from '../../api/adminExcel'
import {
  createAdminGuest,
  generateAdminGuestQrTokens,
  getAdminGuest,
  listAdminGuestFields,
  listAdminGuests,
} from '../../api/adminGuests'
import { getAdminMeeting, updateAdminMeeting } from '../../api/adminMeetings'
import { getApiErrorMessage } from '../../api/client'
import { createStaff, listCheckIns, listStaff } from '../../mock/mockApi'
import { useSessionStore } from '../../stores/session'
import type { CheckInRecord, Guest, GuestField, GuestImportInput, Meeting, MeetingStatus, StaffUser } from '../../types'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const detailLoading = ref(true)
const detailError = ref('')
const guests = ref<Guest[]>([])
const fields = ref<GuestField[]>([])
const staff = ref<StaffUser[]>([])
const checkIns = ref<CheckInRecord[]>([])
const saving = ref(false)
const exporting = ref(false)
const importing = ref(false)
const creatingStaff = ref(false)
const generatingGuestQr = ref(false)
const guestQrMessage = ref('')
const guestQrMessageType = ref<'success' | 'info' | 'error'>('success')
const selectedGuest = ref<Guest>()
const guestDetailDialogVisible = ref(false)
const guestDetailLoading = ref(false)
const guestQrCode = ref('')
const guestCreateDialogVisible = ref(false)
const creatingGuest = ref(false)
const guestForm = ref<GuestImportInput>({ name: '', phone: '', organization: '', title: '', tag: '', seat: '' })
const staffMessage = ref('')
const staffMessageType = ref<'success' | 'error'>('success')
const staffForm = ref({ name: '', phone: '', account: '' })
const guestImportInput = ref<HTMLInputElement>()
const importMessage = ref('')
const importMessageType = ref<'success' | 'warning' | 'error' | 'info'>('success')
const saveMessage = ref('')
const saveMessageType = ref<'success' | 'warning' | 'error' | 'info'>('success')
const editForm = ref({
  title: '',
  description: '',
  location: '',
  startTime: '',
  endTime: '',
  status: 'draft' as MeetingStatus,
})

const checkedCount = computed(() => checkIns.value.length)
const meetingEntryUrl = computed(() => meeting.value ? `${window.location.origin}/meetings/${meeting.value.id}` : '')
const meetingQrCode = ref('')
const meetingQrDialogVisible = ref(false)
const guestRows = computed(() => guests.value.map((guest) => ({
  ...guest,
  checkedIn: checkIns.value.some((record) => record.guestId === guest.id),
})))

/**
 * 加载管理员会议详情页所需数据。
 *
 * 入参：无。
 *
 * 返回值：Promise<void>：加载完成后更新会议、嘉宾、字段、工作人员和签到记录。
 *
 * 异常：会议身份、权限或网络异常时清空详情并展示后端错误；其他资源本阶段仍使用 Mock。
 */
async function loadDetail(): Promise<void> {
  if (!session.admin) {
    detailLoading.value = false
    detailError.value = '请先完成管理员登录。'
    return
  }
  const meetingId = String(route.params.id)
  detailLoading.value = true
  detailError.value = ''
  try {
    const [meetingData, guestData, fieldData, staffData, checkInData] = await Promise.all([
      getAdminMeeting(meetingId),
      listAdminGuests(meetingId),
      listAdminGuestFields(meetingId),
      listStaff(meetingId),
      listCheckIns(meetingId),
    ])
    meeting.value = meetingData
    guests.value = guestData
    fields.value = fieldData
    staff.value = staffData
    checkIns.value = checkInData
    resetEditForm()
  } catch (error) {
    meeting.value = undefined
    detailError.value = getApiErrorMessage(error, '会议详情加载失败。')
  } finally {
    detailLoading.value = false
  }
}

/**
 * 使用当前会议数据重置编辑表单。
 *
 * 入参：
 *   无；函数读取当前页面的会议详情。
 *
 * 返回值：
 *   void：只更新页面编辑表单。
 *
 * 异常：
 *   当前函数不主动抛出异常；会议未加载时直接返回。
 */
function resetEditForm(): void {
  if (!meeting.value) {
    return
  }

  editForm.value = {
    title: meeting.value.title,
    description: meeting.value.description,
    location: meeting.value.location,
    startTime: toDateTimeLocalValue(meeting.value.startTime),
    endTime: toDateTimeLocalValue(meeting.value.endTime),
    status: meeting.value.status,
  }
  saveMessage.value = ''
}

/**
 * 保存会议基础信息编辑结果。
 *
 * 入参：
 *   无；函数从当前路由读取会议 ID，从编辑表单读取会议字段。
 *
 * 返回值：
 *   Promise<void>：保存成功后刷新页面会议详情并展示结果提示。
 *
 * 异常：
 *   字段、时间、权限、登录或网络无效时展示后端错误提示。
 */
async function saveMeeting(): Promise<void> {
  if (!editForm.value.title.trim() || !editForm.value.location.trim()) {
    saveMessageType.value = 'error'
    saveMessage.value = '会议名称和地点不能为空。'
    return
  }

  saving.value = true
  saveMessage.value = ''
  try {
    const savedMeeting = await updateAdminMeeting(String(route.params.id), {
      title: editForm.value.title.trim(),
      description: editForm.value.description.trim(),
      location: editForm.value.location.trim(),
      startTime: toIsoWithChinaTimezone(editForm.value.startTime),
      endTime: toIsoWithChinaTimezone(editForm.value.endTime),
      status: editForm.value.status,
    })
    meeting.value = savedMeeting
    resetEditForm()
    saveMessageType.value = 'success'
    saveMessage.value = '会议信息已保存。'
  } catch (error) {
    saveMessageType.value = 'error'
    saveMessage.value = getApiErrorMessage(error, '会议信息保存失败。')
  } finally {
    saving.value = false
  }
}

/**
 * 根据嘉宾 ID 获取嘉宾姓名。
 *
 * 入参：guestId：嘉宾 ID，必填。
 *
 * 返回值：string：嘉宾姓名；未匹配时返回占位文本。
 *
 * 异常：当前函数不主动抛出异常。
 */
function guestName(guestId: string): string {
  return guests.value.find((guest) => guest.id === guestId)?.name ?? '未知嘉宾'
}

/**
 * 根据工作人员 ID 获取工作人员姓名。
 *
 * 入参：staffId：工作人员 ID，必填。
 *
 * 返回值：string：工作人员姓名；未匹配时返回占位文本。
 *
 * 异常：当前函数不主动抛出异常。
 */
function staffName(staffId: string): string {
  return staff.value.find((item) => item.id === staffId)?.name ?? '未知工作人员'
}

/**
 * 为当前会议所有缺少凭证的嘉宾批量生成个人二维码。
 *
 * 入参：无；函数读取当前会议。
 * 返回值：Promise<void>：生成完成后展示数量摘要。
 * 异常：会议未加载时直接返回；权限、登录或网络异常时展示后端错误。
 */
async function handleGenerateGuestQrTokens(): Promise<void> {
  if (!meeting.value) {
    return
  }
  generatingGuestQr.value = true
  guestQrMessage.value = ''
  try {
    const result = await generateAdminGuestQrTokens(meeting.value.id)
    guestQrMessageType.value = result.generatedCount ? 'success' : 'info'
    guestQrMessage.value = `本次生成 ${result.generatedCount} 个二维码；已有 ${result.existingCount} 个二维码保持不变。`
  } catch (error) {
    guestQrMessageType.value = 'error'
    guestQrMessage.value = getApiErrorMessage(error, '嘉宾二维码生成失败。')
  } finally {
    generatingGuestQr.value = false
  }
}

/**
 * 打开嘉宾详情窗口并生成该嘉宾的个人签到二维码。
 *
 * 入参：guest 为当前列表选中的嘉宾，必填；函数使用其 ID 查询完整资料。
 * 返回值：Promise<void>：详情读取完成后更新嘉宾信息和二维码图片。
 * 异常：权限、网络或二维码生成失败时关闭加载状态并展示错误提示。
 */
async function showGuestDetail(guest: Guest): Promise<void> {
  selectedGuest.value = undefined
  guestQrCode.value = ''
  guestDetailDialogVisible.value = true
  guestDetailLoading.value = true
  try {
    const guestDetail = await getAdminGuest(guest.meetingId, guest.id)
    selectedGuest.value = guestDetail
    guestQrCode.value = await QRCode.toDataURL(guestDetail.qrToken, { width: 220, margin: 1 })
  } catch (error) {
    guestQrCode.value = ''
    guestDetailDialogVisible.value = false
    ElMessage.error(getApiErrorMessage(error, '嘉宾详情或二维码加载失败。'))
  } finally {
    guestDetailLoading.value = false
  }
}

/**
 * 创建嘉宾并刷新当前会议嘉宾列表。
 *
 * 入参：无；读取当前会议和新增嘉宾表单。
 * 返回值：Promise<void>：创建完成后关闭弹窗并更新列表。
 * 异常：姓名或手机号缺失、权限、登录或网络异常时显示错误提示。
 */
async function handleCreateGuest(): Promise<void> {
  if (!meeting.value || !guestForm.value.name.trim() || !guestForm.value.phone.trim()) {
    ElMessage.warning('请填写嘉宾姓名和手机号。')
    return
  }
  creatingGuest.value = true
  try {
    await createAdminGuest(meeting.value.id, guestForm.value)
    guests.value = await listAdminGuests(meeting.value.id)
    guestForm.value = { name: '', phone: '', organization: '', title: '', tag: '', seat: '' }
    guestCreateDialogVisible.value = false
    ElMessage.success('嘉宾已新增，并已生成个人二维码。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '嘉宾新增失败。'))
  } finally {
    creatingGuest.value = false
  }
}

/**
 * 创建工作人员账号并授权其负责当前会议。
 *
 * 入参：无；读取当前会议与工作人员表单。
 * 返回值：Promise<void>：创建后刷新工作人员列表并展示结果。
 * 异常：必填字段缺失、会议不存在或账号重复时展示错误提示。
 */
async function handleCreateStaff(): Promise<void> {
  if (!meeting.value || !staffForm.value.name.trim() || !staffForm.value.phone.trim() || !staffForm.value.account.trim()) {
    staffMessageType.value = 'error'
    staffMessage.value = '请完整填写姓名、手机号和登录账号。'
    return
  }
  creatingStaff.value = true
  const created = await createStaff(meeting.value.id, { name: staffForm.value.name.trim(), phone: staffForm.value.phone.trim(), account: staffForm.value.account.trim() })
  creatingStaff.value = false
  if (!created) {
    staffMessageType.value = 'error'
    staffMessage.value = '创建失败：账号已存在或会议不存在。'
    return
  }
  staff.value = await listStaff(meeting.value.id)
  staffForm.value = { name: '', phone: '', account: '' }
  staffMessageType.value = 'success'
  staffMessage.value = '工作人员已创建并授权当前会议。'
}

/**
 * 下载包含标准列名的嘉宾 Excel 导入模板。
 *
 * 入参：无。
 *
 * 返回值：void：浏览器开始下载 xlsx 模板文件。
 *
 * 异常：当前函数不主动抛出异常；浏览器禁止下载时由浏览器提示。
 */
async function downloadGuestImportTemplate(): Promise<void> {
  if (!meeting.value) {
    return
  }
  try {
    await downloadAdminGuestImportTemplate(meeting.value.id, meeting.value.title)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '嘉宾导入模板下载失败。'))
  }
}

/**
 * 打开系统文件选择器，以便管理员选择待导入的 Excel 文件。
 *
 * 入参：无。
 *
 * 返回值：void：触发隐藏文件输入框的点击事件。
 *
 * 异常：当前函数不主动抛出异常；输入框未挂载时直接返回。
 */
function openGuestImportFilePicker(): void {
  guestImportInput.value?.click()
}

/**
 * 将管理员选择的 Excel 文件上传后端并展示逐行导入结果。
 *
 * 入参：
 *   event：文件输入框变化事件，必填。
 *
 * 返回值：Promise<void>：导入结束后刷新嘉宾列表并显示结果摘要。
 *
 * 异常：
 *   文件格式、大小、表头、字段值、权限或网络异常时显示后端错误提示。
 */
async function handleGuestImportFileChange(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file || !meeting.value) {
    return
  }

  importing.value = true
  importMessage.value = ''

  try {
    const result = await importAdminGuests(meeting.value.id, file)
    guests.value = await listAdminGuests(meeting.value.id)
    importMessageType.value = result.errors.length ? 'warning' : 'success'
    importMessage.value = result.errors.length
      ? `成功导入 ${result.importedCount} 名嘉宾；${result.errors.map((item) => `第 ${item.rowNumber} 行：${item.message}`).join('；')}`
      : `成功导入 ${result.importedCount} 名嘉宾。`
  } catch (error) {
    importMessageType.value = 'error'
    importMessage.value = getApiErrorMessage(error, '导入失败，请检查 Excel 文件后重试。')
  } finally {
    importing.value = false
    input.value = ''
  }
}

/**
 * 将当前会议的全量嘉宾签到表导出为 xlsx 文件。
 *
 * 入参：
 *   无；函数读取已加载的会议、嘉宾和签到记录。
 *
 * 返回值：
 *   Promise<void>：后端生成并下载 Excel 文件后结束。
 *
 * 异常：
 *   会议未加载、权限或网络失败时展示页面提示，不向页面外抛出异常。
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
    await downloadAdminCheckInExport(meeting.value.id, meeting.value.title)
    ElMessage.success('嘉宾签到表已开始下载。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '签到表导出失败，请稍后重试。'))
  } finally {
    exporting.value = false
  }
}

/**
 * 跳转到管理员登录页。
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
 * 返回管理员会议管理列表。
 *
 * 入参：无。
 * 返回值：void：触发前端路由跳转。
 * 异常：当前函数不主动抛出异常。
 */
function goMeetings(): void {
  router.push('/admin/meetings')
}

/**
 * 复制当前已发布会议的公开入口链接。
 *
 * 入参：无；函数读取当前会议入口链接。
 * 返回值：Promise<void>：复制完成后展示操作结果。
 * 异常：浏览器不允许访问剪贴板时展示错误提示。
 */
async function copyMeetingEntryUrl(): Promise<void> {
  try {
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(meetingEntryUrl.value)
      } catch {
        copyMeetingEntryUrlBySelection()
      }
    } else {
      copyMeetingEntryUrlBySelection()
    }
    ElMessage.success('会议入口链接已复制。')
  } catch {
    ElMessage.error('复制失败，请手动复制链接。')
  }
}

/**
 * 使用文本选择方式复制会议入口链接，兼容不允许异步剪贴板访问的浏览器。
 *
 * 入参：无；函数读取当前会议入口链接。
 * 返回值：void：执行浏览器复制命令。
 * 异常：浏览器拒绝复制命令时抛出异常，由调用方展示错误提示。
 */
function copyMeetingEntryUrlBySelection(): void {
  const textArea = document.createElement('textarea')
  textArea.value = meetingEntryUrl.value
  document.body.appendChild(textArea)
  textArea.select()
  const copied = document.execCommand('copy')
  textArea.remove()
  if (!copied) {
    throw new Error('浏览器拒绝复制命令。')
  }
}

/**
 * 打开会议二维码查看与下载窗口。
 *
 * 入参：无。
 * 返回值：void：显示会议二维码弹窗。
 * 异常：当前函数不主动抛出异常。
 */
function openMeetingQrDialog(): void {
  meetingQrDialogVisible.value = true
}

/**
 * 下载当前会议入口二维码图片。
 *
 * 入参：无；函数读取已生成的二维码数据地址和会议 ID。
 * 返回值：Promise<void>：生成包含会议标题、二维码和时间的 PNG 后触发下载。
 * 异常：二维码尚未生成、图片加载或画布创建失败时展示提示。
 */
async function downloadMeetingQrCode(): Promise<void> {
  if (!meetingQrCode.value || !meeting.value) {
    ElMessage.warning('二维码尚未生成。')
    return
  }
  const currentMeeting = meeting.value
  const canvas = document.createElement('canvas')
  const width = 600
  const height = 780
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext('2d')
  if (!context) {
    ElMessage.error('二维码下载失败，请稍后重试。')
    return
  }
  context.fillStyle = '#ffffff'
  context.fillRect(0, 0, width, height)
  context.fillStyle = '#111827'
  context.textAlign = 'center'
  context.font = '600 30px "Microsoft YaHei"'
  context.fillText(currentMeeting.title, width / 2, 64)
  let image: HTMLImageElement
  try {
    image = await loadQrImage(meetingQrCode.value)
  } catch {
    ElMessage.error('二维码下载失败，请稍后重试。')
    return
  }
  context.drawImage(image, 110, 110, 380, 380)
  context.fillStyle = '#4b5563'
  context.font = '24px "Microsoft YaHei"'
  context.fillText(`${formatDate(currentMeeting.startTime)} - ${formatDate(currentMeeting.endTime)}`, width / 2, 560)
  const link = document.createElement('a')
  link.href = canvas.toDataURL('image/png')
  link.download = `${currentMeeting.title.replace(/[\\/:*?"<>|]/g, '_')}-会议入口二维码.png`
  link.click()
}

/**
 * 加载二维码数据地址对应的图片，供下载排版画布绘制。
 *
 * 入参：source 为二维码图片数据地址，必填。
 * 返回值：Promise<HTMLImageElement>：成功加载的图片对象。
 * 异常：图片加载失败时拒绝 Promise。
 */
function loadQrImage(source: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('二维码图片加载失败。'))
    image.src = source
  })
}

/**
 * 根据已发布会议入口链接生成可扫码的二维码图片。
 *
 * 入参：entryUrl 为会议入口 URL，必填；为空或会议未发布时清空二维码。
 * 返回值：Promise<void>：完成后更新页面二维码数据地址。
 * 异常：二维码生成失败时清空图片并提示管理员。
 */
async function generateMeetingEntryQrCode(entryUrl: string): Promise<void> {
  if (!meeting.value || meeting.value.status !== 'published' || !entryUrl) {
    meetingQrCode.value = ''
    return
  }
  try {
    meetingQrCode.value = await QRCode.toDataURL(entryUrl, { width: 220, margin: 1 })
  } catch {
    meetingQrCode.value = ''
    ElMessage.error('会议二维码生成失败，请稍后重试。')
  }
}

/**
 * 格式化日期时间展示。
 *
 * 入参：value：ISO 日期字符串，必填。
 *
 * 返回值：string：中文本地化日期时间。
 *
 * 异常：当前函数不主动抛出异常。
 */
function formatDate(value: string): string {
  return new Date(value).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}

/**
 * 将 ISO 日期字符串转换为 datetime-local 控件可识别的值。
 *
 * 入参：
 *   value：ISO 日期字符串，必填。
 *
 * 返回值：
 *   string：形如 yyyy-MM-ddTHH:mm 的本地表单值。
 *
 * 异常：
 *   当前函数不主动抛出异常；空值会返回空字符串。
 */
function toDateTimeLocalValue(value: string): string {
  return value.slice(0, 16)
}

/**
 * 将 datetime-local 表单值转换为带中国时区偏移的 ISO 字符串。
 *
 * 入参：
 *   value：datetime-local 表单值，必填，格式通常为 yyyy-MM-ddTHH:mm。
 *
 * 返回值：
 *   string：形如 yyyy-MM-ddTHH:mm:00+08:00 的时间字符串。
 *
 * 异常：
 *   当前函数不主动抛出异常；空值会返回空字符串。
 */
function toIsoWithChinaTimezone(value: string): string {
  return value ? `${value}:00+08:00` : ''
}

onMounted(loadDetail)
watch(meetingEntryUrl, generateMeetingEntryQrCode, { immediate: true })
</script>
