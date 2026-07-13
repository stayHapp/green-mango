<template>
  <section class="page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">工作人员端</p>
        <h1>负责会议</h1>
        <p class="muted">{{ session.staff ? `${session.staff.name} 的签到任务` : '请先完成工作人员登录。' }}</p>
      </div>
      <el-button v-if="!session.staff" type="primary" @click="goLogin">去登录</el-button>
    </div>

    <el-empty v-if="!session.staff" description="暂无工作人员会话" />
    <el-table v-else :data="meetings" class="data-table" row-key="id">
      <el-table-column prop="title" label="会议名称" min-width="220" />
      <el-table-column prop="location" label="地点" min-width="200" />
      <el-table-column label="时间" min-width="260">
        <template #default="{ row }">{{ formatDate(row.startTime) }} - {{ formatDate(row.endTime) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="goCheckIn(row.id)">签到</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { listStaffMeetings } from '../../mock/mockApi'
import { useSessionStore } from '../../stores/session'
import type { Meeting } from '../../types'

const router = useRouter()
const session = useSessionStore()
const meetings = ref<Meeting[]>([])

/**
 * 加载当前工作人员负责的会议。
 *
 * 入参：
 *   无；函数从 Pinia（状态管理库）会话中读取当前工作人员 ID。
 *
 * 返回值：
 *   Promise<void>：加载完成后更新工作人员会议列表。
 *
 * 异常：
 *   当前 mock API 不主动抛出异常；未登录时直接跳过加载。
 */
async function loadMeetings(): Promise<void> {
  if (!session.staff) {
    meetings.value = []
    return
  }

  meetings.value = await listStaffMeetings(session.staff.id)
}

/**
 * 跳转到工作人员登录页。
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
 * 跳转到会议签到页。
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
function goCheckIn(meetingId: string): void {
  router.push(`/staff/meetings/${meetingId}/check-in`)
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

onMounted(loadMeetings)
</script>
