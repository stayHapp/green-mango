<template>
  <section v-if="meeting" class="page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">管理员端</p>
        <h1>{{ meeting.title }}</h1>
        <p class="muted">{{ meeting.location }}｜{{ formatDate(meeting.startTime) }} - {{ formatDate(meeting.endTime) }}</p>
      </div>
      <div class="heading-actions">
        <el-button v-if="!session.admin" type="primary" @click="goLogin">去登录</el-button>
        <el-tag type="success">签到 {{ checkedCount }}/{{ guests.length }}</el-tag>
      </div>
    </div>

    <el-alert v-if="!session.admin" class="top-gap" type="warning" :closable="false" title="请先完成管理员登录后再查看和编辑会议。" />

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
        </el-table>
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
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getMeeting, listCheckIns, listGuestFields, listGuests, listStaff, updateMeeting } from '../../mock/mockApi'
import { useSessionStore } from '../../stores/session'
import type { CheckInRecord, Guest, GuestField, Meeting, MeetingStatus, StaffUser } from '../../types'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const guests = ref<Guest[]>([])
const fields = ref<GuestField[]>([])
const staff = ref<StaffUser[]>([])
const checkIns = ref<CheckInRecord[]>([])
const saving = ref(false)
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
 * 异常：当前 mock API 不主动抛出异常；真实 API 失败时需要补充错误处理。
 */
async function loadDetail(): Promise<void> {
  const meetingId = String(route.params.id)
  const [meetingData, guestData, fieldData, staffData, checkInData] = await Promise.all([
    getMeeting(meetingId),
    listGuests(meetingId),
    listGuestFields(meetingId),
    listStaff(meetingId),
    listCheckIns(meetingId),
  ])
  meeting.value = meetingData
  guests.value = guestData
  fields.value = fieldData
  staff.value = staffData
  checkIns.value = checkInData
  resetEditForm()
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
 *   mock API 当前不主动抛出异常；字段缺失或会议不存在时展示页面错误提示。
 */
async function saveMeeting(): Promise<void> {
  if (!editForm.value.title.trim() || !editForm.value.location.trim()) {
    saveMessageType.value = 'error'
    saveMessage.value = '会议名称和地点不能为空。'
    return
  }

  saving.value = true
  const savedMeeting = await updateMeeting(String(route.params.id), {
    title: editForm.value.title.trim(),
    description: editForm.value.description.trim(),
    location: editForm.value.location.trim(),
    startTime: toIsoWithChinaTimezone(editForm.value.startTime),
    endTime: toIsoWithChinaTimezone(editForm.value.endTime),
    status: editForm.value.status,
  })
  saving.value = false

  if (!savedMeeting) {
    saveMessageType.value = 'error'
    saveMessage.value = '保存失败，未找到当前会议。'
    return
  }

  meeting.value = savedMeeting
  resetEditForm()
  saveMessageType.value = 'success'
  saveMessage.value = '会议信息已保存。'
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
</script>
