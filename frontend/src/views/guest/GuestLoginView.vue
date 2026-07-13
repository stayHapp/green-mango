<template>
  <section class="page guest-portal-page">
    <div v-if="meeting" class="guest-meeting-hero">
      <div>
        <p class="eyebrow">嘉宾端</p>
        <h1>{{ meeting.title }}</h1>
        <p class="lead">{{ meeting.description }}</p>
        <dl class="compact-info-list">
          <dt>时间</dt>
          <dd>{{ formatDate(meeting.startTime) }} - {{ formatDate(meeting.endTime) }}</dd>
          <dt>地点</dt>
          <dd>{{ meeting.location }}</dd>
        </dl>
      </div>
      <el-tag type="success">扫码进入</el-tag>
    </div>
    <el-empty v-else description="未找到会议入口" />

    <el-card v-if="meeting && !currentGuest" shadow="never" class="form-card">
      <template #header>身份验证</template>
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="姓名">
          <el-input v-model="name" placeholder="请输入嘉宾姓名" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="phone" placeholder="请输入手机号" />
        </el-form-item>
        <div class="action-row">
          <el-button @click="fillDemoGuest">填入示例</el-button>
          <el-button type="primary" :loading="loading" @click="handleLogin">登录</el-button>
        </div>
      </el-form>
      <el-alert v-if="errorMessage" class="top-gap" type="error" :closable="false" :title="errorMessage" />
    </el-card>

    <div v-if="meeting && currentGuest" class="guest-content-stack">
      <el-card shadow="never" class="guest-pass-card">
        <div class="identity-panel">
          <div>
            <div class="identity-name">{{ currentGuest.name }}</div>
            <div class="identity-role">{{ currentGuest.tag }}</div>
          </div>
        </div>
        <dl class="info-list top-gap">
          <dt>电话</dt>
          <dd>{{ currentGuest.phone }}</dd>
          <dt>单位</dt>
          <dd>{{ currentGuest.organization }}</dd>
          <dt>职务</dt>
          <dd>{{ currentGuest.title }}</dd>
          <dt>座位</dt>
          <dd>{{ currentGuest.seat }}</dd>
        </dl>
        <div class="qr-token guest-pass-qr">{{ currentGuest.qrToken }}</div>
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
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { getMeeting, listMeetings, loginGuest } from '../../mock/mockApi'
import { useSessionStore } from '../../stores/session'
import type { Guest, Meeting } from '../../types'

interface FeatureMenuItem {
  key: string
  title: string
  description: string
}

const route = useRoute()
const session = useSessionStore()
const meeting = ref<Meeting>()
const name = ref('')
const phone = ref('')
const loading = ref(false)
const errorMessage = ref('')
const featureMessage = ref('')
const currentGuest = computed(() => {
  if (!meeting.value || session.guest?.meetingId !== meeting.value.id) {
    return undefined
  }

  return session.guest
})
const featureMenus: FeatureMenuItem[] = [
  { key: 'agenda', title: '会议日程', description: '查看当天流程和环节安排' },
  { key: 'manual', title: '会议手册', description: '查看会务资料和注意事项' },
  { key: 'weather', title: '天气情况', description: '了解到场当天城市天气' },
  { key: 'route', title: '路线指引', description: '查看会场位置和交通建议' },
  { key: 'contact', title: '联系我们', description: '联系会务组和现场支持' },
]

/**
 * 加载扫码入口对应的会议信息。
 *
 * 入参：
 *   无；函数优先读取 URL 中的 meetingId 参数，缺省时使用 mock 数据中的第一个会议。
 *
 * 返回值：
 *   Promise<void>：加载完成后更新页面会议信息。
 *
 * 异常：
 *   当前 mock API 不主动抛出异常；会议不存在时页面展示空状态。
 */
async function loadMeeting(): Promise<void> {
  const meetingId = route.query.meetingId ? String(route.query.meetingId) : ''

  if (meetingId) {
    meeting.value = await getMeeting(meetingId)
    return
  }

  const meetings = await listMeetings()
  meeting.value = meetings[0]
}

/**
 * 使用 mock 数据填入一组嘉宾登录示例。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：只更新当前表单字段。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function fillDemoGuest(): void {
  name.value = '李文博'
  phone.value = '13900000001'
  errorMessage.value = ''
}

/**
 * 执行嘉宾端 mock 登录。
 *
 * 入参：
 *   无；函数从页面表单中读取姓名和手机号，两个字段均必填。
 *
 * 返回值：
 *   Promise<void>：登录成功后保存嘉宾会话并跳转到嘉宾会议列表。
 *
 * 异常：
 *   mock API 当前不主动抛出异常；匹配不到嘉宾时展示页面错误提示。
 */
async function handleLogin(): Promise<void> {
  errorMessage.value = ''

  if (!meeting.value) {
    errorMessage.value = '当前会议入口无效，无法登录。'
    return
  }

  if (!name.value.trim() || !phone.value.trim()) {
    errorMessage.value = '请填写姓名和手机号。'
    return
  }

  loading.value = true
  const guest = await loginGuest(name.value.trim(), phone.value.trim())
  loading.value = false

  if (!guest) {
    errorMessage.value = '未找到匹配的嘉宾，请检查 mock 登录信息。'
    return
  }

  if (guest.meetingId !== meeting.value.id) {
    errorMessage.value = '该嘉宾不属于当前会议，请核对入口二维码。'
    return
  }

  session.setGuest(guest)
  featureMessage.value = ''
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

onMounted(loadMeeting)
</script>
