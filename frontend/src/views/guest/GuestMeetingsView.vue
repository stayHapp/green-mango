<template>
  <section class="page narrow-page guest-route-bridge">
    <div v-if="session.guest" v-loading="true" class="page-loading-block" aria-label="正在进入当前会议" />
    <el-empty v-else description="嘉宾身份仅在会议专属入口中核验">
      <el-button type="primary" @click="goHome">返回系统首页</el-button>
    </el-empty>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useSessionStore } from '../../stores/session'

const router = useRouter()
const session = useSessionStore()

/**
 * 将历史嘉宾会议列表路由兼容跳转到会话所属的当前会议。
 *
 * 入参：无；函数读取 Pinia（状态管理库）中的会议级嘉宾身份。
 * 返回值：Promise<void>：存在嘉宾会话时完成当前会议详情路由替换；未登录时保留说明页。
 * 异常：路由替换失败时由 Vue Router 抛出异常。
 */
async function redirectToCurrentMeeting(): Promise<void> {
  if (!session.guest) {
    return
  }
  await router.replace(`/guest/meetings/${session.guest.meetingId}`)
}

/**
 * 返回系统首页以重新获取会议专属入口。
 *
 * 入参：无。
 * 返回值：Promise<void>：完成首页路由跳转。
 * 异常：路由跳转失败时由 Vue Router 抛出异常。
 */
async function goHome(): Promise<void> {
  await router.push('/')
}

onMounted(redirectToCurrentMeeting)
</script>
