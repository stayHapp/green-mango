<template>
  <section class="page">
    <div class="page-heading">
      <div>
        <h1>{{ meeting?.title ?? '会议详情' }}</h1>
        <dl v-if="meeting" class="compact-info-list">
          <dt>时间</dt>
          <dd>{{ formatDate(meeting.startTime) }} - {{ formatDate(meeting.endTime) }}</dd>
          <dt>地点</dt>
          <dd>{{ meeting.location }}</dd>
        </dl>
        <p v-else class="muted">请先选择会议。</p>
      </div>
      <el-button v-if="!session.guest" type="primary" @click="goLogin">去登录</el-button>
    </div>

    <el-empty v-if="!session.guest" description="暂无嘉宾会话" />
    <el-empty v-else-if="!meeting" description="未找到会议" />
    <div v-else class="guest-content-stack">
      <el-card shadow="never" class="guest-pass-card">
        <div class="identity-panel">
          <div class="guest-identity-heading">
            <div class="identity-name">{{ session.guest.name }}</div>
            <el-tag class="identity-role" type="success" effect="light">{{ session.guest.tag }}</el-tag>
          </div>
          <el-button type="primary" plain @click="openFeatureDrawer">会议功能</el-button>
        </div>
        <dl class="info-list">
          <dt>电话</dt>
          <dd>{{ session.guest.phone }}</dd>
          <dt>单位</dt>
          <dd>{{ session.guest.organization }}</dd>
          <dt>职务</dt>
          <dd>{{ session.guest.title }}</dd>
          <dt>座位</dt>
          <dd>{{ session.guest.seat }}</dd>
        </dl>
        <GuestQrCode :meeting-id="meeting.id" :token="session.guest.qrToken" />
      </el-card>

    </div>

    <el-drawer v-model="featureDrawerVisible" title="会议功能" direction="rtl" size="min(360px, 88vw)">
      <MeetingAssistantMenu :meeting-id="String(route.params.id)" />
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getMeeting } from '../../mock/mockApi'
import { useSessionStore } from '../../stores/session'
import type { Meeting } from '../../types'
import GuestQrCode from '../../components/GuestQrCode.vue'
import MeetingAssistantMenu from '../../components/MeetingAssistantMenu.vue'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const featureDrawerVisible = ref(false)

/**
 * 加载嘉宾会议详情。
 *
 * 入参：
 *   无；函数从当前路由参数读取会议 ID。
 *
 * 返回值：
 *   Promise<void>：加载完成后更新会议详情。
 *
 * 异常：
 *   当前 mock API 不主动抛出异常；会议不存在时页面展示空状态。
 */
async function loadDetail(): Promise<void> {
  meeting.value = await getMeeting(String(route.params.id))
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
  router.push(`/guest/login?meetingId=${String(route.params.id)}`)
}

/**
 * 展开会议功能侧边面板并清除上一次功能提示。
 *
 * 入参：无。
 * 返回值：void：显示右侧会议功能面板。
 * 异常：当前函数不主动抛出异常。
 */
function openFeatureDrawer(): void {
  featureDrawerVisible.value = true
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

onMounted(loadDetail)
</script>
