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
    <el-table v-else :data="meetings" class="data-table" row-key="id">
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
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { listAdminMeetings } from '../../mock/mockApi'
import { useSessionStore } from '../../stores/session'
import type { Meeting, MeetingStatus } from '../../types'

const router = useRouter()
const session = useSessionStore()
const meetings = ref<Meeting[]>([])

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
