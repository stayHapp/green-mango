<template>
  <section class="page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">嘉宾端</p>
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
          <div>
            <div class="identity-name">{{ session.guest.name }}</div>
            <div class="identity-role">{{ session.guest.tag }}</div>
          </div>
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
        <div class="qr-token guest-pass-qr">{{ session.guest.qrToken }}</div>
      </el-card>

      <el-card shadow="never">
        <div class="feature-menu-grid">
          <button v-for="item in featureMenus" :key="item.title" class="feature-menu-item" type="button" @click="openFeature(item)">
            <span class="feature-menu-title">{{ item.title }}</span>
            <span class="feature-menu-desc">{{ item.description }}</span>
          </button>
        </div>
        <el-alert v-if="featureMessage" class="top-gap" type="info" :closable="false" :title="featureMessage" />
      </el-card>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getMeeting } from '../../mock/mockApi'
import { useSessionStore } from '../../stores/session'
import type { Meeting } from '../../types'

interface FeatureMenuItem {
  key: string
  title: string
  description: string
}

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const featureMessage = ref('')
const featureMenus: FeatureMenuItem[] = [
  { key: 'agenda', title: '会议日程', description: '查看当天流程和环节安排' },
  { key: 'manual', title: '会议手册', description: '查看会务资料和注意事项' },
  { key: 'weather', title: '天气情况', description: '了解到场当天城市天气' },
  { key: 'route', title: '路线指引', description: '查看会场位置和交通建议' },
  { key: 'contact', title: '联系我们', description: '联系会务组和现场支持' },
]

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
  router.push(`/login?meetingId=${String(route.params.id)}`)
}

/**
 * 打开嘉宾端功能菜单。
 *
 * 入参：
 *   item：功能菜单项，必填，包含功能标识、标题和说明。
 *
 * 返回值：
 *   void：根据菜单项更新当前页面展示状态。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function openFeature(item: FeatureMenuItem): void {
  featureMessage.value = `${item.title} 功能将在后续版本接入正式内容。`
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
