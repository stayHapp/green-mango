<template>
  <section class="page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">管理员端</p>
        <h1>会议管理</h1>
        <p class="muted">{{ session.admin ? `${session.admin.name} 可管理的会议` : '请先完成管理员登录。' }}</p>
      </div>
      <el-button v-if="!session.admin" type="primary" @click="goLogin">去登录</el-button>
    </div>

    <el-empty v-if="!session.admin" description="暂无管理员会话" />
    <template v-else>
      <el-table :data="meetings" class="data-table top-gap" row-key="id">
      <el-table-column prop="title" label="会议名称" min-width="220" />
      <el-table-column prop="location" label="地点" min-width="220" />
      <el-table-column label="时间" min-width="260">
        <template #default="{ row }">{{ formatDate(row.startTime) }} - {{ formatDate(row.endTime) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="row.status === 'published' ? 'success' : 'warning'">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="goDetail(row.id)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
      <div class="action-row top-gap"><el-button type="primary" @click="openCreateMeetingDialog">创建会议</el-button></div>
      <el-dialog v-model="createDialogVisible" title="创建会议" width="min(560px, calc(100% - 32px))">
        <el-form label-position="top" @submit.prevent>
          <div class="form-grid"><el-form-item label="会议名称"><el-input v-model="createForm.title" /></el-form-item><el-form-item label="会议地点"><el-input v-model="createForm.location" /></el-form-item></div>
          <el-form-item label="会议说明"><el-input v-model="createForm.description" type="textarea" /></el-form-item>
          <div class="form-grid"><el-form-item label="开始时间"><el-input v-model="createForm.startTime" type="datetime-local" /></el-form-item><el-form-item label="结束时间"><el-input v-model="createForm.endTime" type="datetime-local" /></el-form-item></div>
          <div class="action-row"><el-button type="primary" :loading="creating" @click="handleCreateMeeting">创建会议</el-button></div>
          <el-alert v-if="createMessage" class="top-gap" :type="createMessageType" :closable="false" :title="createMessage" />
        </el-form>
      </el-dialog>
    </template>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { createMeeting, listAdminMeetings } from '../../mock/mockApi'
import { useSessionStore } from '../../stores/session'
import type { Meeting, MeetingStatus } from '../../types'

const router = useRouter()
const session = useSessionStore()
const meetings = ref<Meeting[]>([])
const creating = ref(false)
const createMessage = ref('')
const createMessageType = ref<'success' | 'error'>('success')
const createDialogVisible = ref(false)
const createForm = ref({ title: '', location: '', description: '', startTime: '', endTime: '' })

/**
 * 加载管理员端会议列表。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   Promise<void>：加载完成后更新页面会议列表。
 *
 * 异常：
 *   mock API 当前不主动抛出异常；后续真实 API 失败时需要补充错误提示。
 */
async function loadMeetings(): Promise<void> {
  if (!session.admin) {
    meetings.value = []
    return
  }

  meetings.value = await listAdminMeetings(session.admin.id)
}

/**
 * 创建新会议并刷新当前管理员的会议列表。
 *
 * 入参：无；函数读取当前管理员和创建表单。
 * 返回值：Promise<void>：创建完成后更新会议列表与提示信息。
 * 异常：管理员未登录或会议名称、地点缺失时显示错误提示。
 */
async function handleCreateMeeting(): Promise<void> {
  if (!session.admin || !createForm.value.title.trim() || !createForm.value.location.trim()) {
    createMessageType.value = 'error'
    createMessage.value = '请填写会议名称和地点。'
    return
  }
  creating.value = true
  await createMeeting(session.admin.id, { title: createForm.value.title.trim(), location: createForm.value.location.trim(), description: createForm.value.description.trim(), startTime: createForm.value.startTime ? `${createForm.value.startTime}:00+08:00` : '', endTime: createForm.value.endTime ? `${createForm.value.endTime}:00+08:00` : '', status: 'draft' })
  creating.value = false
  createForm.value = { title: '', location: '', description: '', startTime: '', endTime: '' }
  createMessageType.value = 'success'
  createMessage.value = '会议已创建。'
  await loadMeetings()
  createDialogVisible.value = false
}

/**
 * 打开创建会议弹窗并清除上次提示信息。
 *
 * 入参：无。
 * 返回值：void：显示创建会议表单。
 * 异常：当前函数不主动抛出异常。
 */
function openCreateMeetingDialog(): void {
  createMessage.value = ''
  createDialogVisible.value = true
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
 * 跳转到会议详情页。
 *
 * 入参：
 *   meetingId：会议 ID，必填。
 *
 * 返回值：
 *   void：只触发前端路由跳转。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function goDetail(meetingId: string): void {
  router.push(`/admin/meetings/${meetingId}`)
}

/**
 * 格式化日期时间展示。
 *
 * 入参：
 *   value：ISO 日期字符串，必填。
 *
 * 返回值：
 *   string：适合页面展示的本地日期时间。
 *
 * 异常：
 *   日期字符串非法时浏览器会返回 Invalid Date 文本，后续真实数据应在接口层校验。
 */
function formatDate(value: string): string {
  return new Date(value).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}

/**
 * 将会议状态转换为中文展示文本。
 *
 * 入参：
 *   status：会议状态，必填。
 *
 * 返回值：
 *   string：中文状态文本。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function statusText(status: MeetingStatus): string {
  const map: Record<MeetingStatus, string> = {
    draft: '草稿',
    published: '已发布',
    ended: '已结束',
  }
  return map[status]
}

onMounted(loadMeetings)
</script>
