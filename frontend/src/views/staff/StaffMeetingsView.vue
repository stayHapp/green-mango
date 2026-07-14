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
    <el-empty v-else-if="!meetings.length" description="暂无负责会议" />
    <div v-else class="staff-meeting-list">
      <article v-for="meeting in meetings" :key="meeting.id" class="staff-meeting-card">
        <h2>{{ meeting.title }}</h2>
        <el-button type="primary" @click="goCheckIn(meeting.id)">签到</el-button>
      </article>
    </div>
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

onMounted(loadMeetings)
</script>
