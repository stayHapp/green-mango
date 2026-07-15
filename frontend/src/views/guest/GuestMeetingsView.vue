<template>
  <section class="page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">嘉宾端</p>
        <h1>我的会议</h1>
        <p class="muted">{{ session.guest ? `${session.guest.name} 的参会安排` : '请先完成嘉宾登录。' }}</p>
      </div>
      <el-button v-if="!session.guest" type="primary" @click="goLogin">去登录</el-button>
    </div>

    <el-empty v-if="!session.guest" description="暂无嘉宾会话" />
    <el-table v-else :data="meetings" class="data-table" row-key="id">
      <el-table-column prop="title" label="会议名称" min-width="220" />
      <el-table-column prop="location" label="地点" min-width="200" />
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
          <el-button type="primary" size="small" @click="goDetail(row.id)">查看二维码</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { listGuestMeetings } from '../../mock/mockApi'
import { useSessionStore } from '../../stores/session'
import type { Meeting, MeetingStatus } from '../../types'

const router = useRouter()
const session = useSessionStore()
const meetings = ref<Meeting[]>([])

/**
 * 加载当前嘉宾可参加的会议。
 *
 * 入参：
 *   无；函数从 Pinia（状态管理库）会话中读取当前嘉宾 ID。
 *
 * 返回值：
 *   Promise<void>：加载完成后更新嘉宾会议列表。
 *
 * 异常：
 *   当前 mock API 不主动抛出异常；未登录时直接跳过加载。
 */
async function loadMeetings(): Promise<void> {
  if (!session.guest) {
    meetings.value = []
    return
  }

  meetings.value = await listGuestMeetings(session.guest.id)
}

/**
 * 跳转到嘉宾登录页。
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
  router.push('/guest/login?meetingId=m-edu-2026')
}

/**
 * 跳转到嘉宾会议详情页。
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
  router.push(`/guest/meetings/${meetingId}`)
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
 * 将会议状态转换为中文展示文本。
 *
 * 入参：
 *   status：会议状态，必填，可取 draft、published 或 ended。
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
