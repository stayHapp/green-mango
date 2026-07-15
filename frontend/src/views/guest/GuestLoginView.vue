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
          <div class="guest-identity-heading">
            <div class="identity-name">{{ currentGuest.name }}</div>
            <el-tag class="identity-role" type="success" effect="light">{{ currentGuest.tag }}</el-tag>
          </div>
          <el-button type="primary" plain @click="openFeatureDrawer">会议功能</el-button>
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
        <GuestQrCode :token="currentGuest.qrToken" />
      </el-card>

    </div>

    <el-drawer v-model="featureDrawerVisible" title="会议功能" direction="rtl" size="min(360px, 88vw)">
      <div class="feature-drawer-list">
        <button v-for="item in featureMenus" :key="item.key" class="feature-menu-item" type="button" @click="openFeature(item)">
          <span class="feature-menu-title">{{ item.title }}</span>
          <span class="feature-menu-desc">{{ item.description }}</span>
        </button>
      </div>
      <el-alert v-if="featureMessage" class="top-gap" type="info" :closable="false" :title="featureMessage" />
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { getApiErrorMessage } from '../../api/client'
import { getPublicMeeting, loginGuest } from '../../api/sessions'
import { useSessionStore } from '../../stores/session'
import type { Guest, Meeting } from '../../types'
import GuestQrCode from '../../components/GuestQrCode.vue'

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
const featureDrawerVisible = ref(false)
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
 * 嘉宾会话被清除时同步清空身份表单和功能提示。
 *
 * 入参：guest 为当前 Pinia 嘉宾状态；退出后为 undefined。
 * 返回值：void：只更新当前页面的敏感表单和提示状态。
 * 异常：当前函数不主动抛出异常。
 */
function clearIdentityAfterLogout(guest: Guest | undefined): void {
  if (guest) {
    return
  }
  name.value = ''
  phone.value = ''
  errorMessage.value = ''
  featureMessage.value = ''
  featureDrawerVisible.value = false
}

watch(() => session.guest, clearIdentityAfterLogout)

/**
 * 加载扫码入口对应的会议信息。
 *
 * 入参：
 *   无；函数读取 URL 中的 meetingId 参数，并调用公开会议 API。
 *
 * 返回值：
 *   Promise<void>：加载完成后更新页面会议信息。
 *
 * 异常：
 *   会议不存在、尚未发布或后端不可用时清空会议信息并展示错误提示。
 */
async function loadMeeting(): Promise<void> {
  const meetingId = route.query.meetingId ? String(route.query.meetingId) : ''

  if (!meetingId) {
    errorMessage.value = '缺少会议入口 ID，请通过会议二维码进入。'
    return
  }
  try {
    meeting.value = await getPublicMeeting(meetingId)
  } catch (error) {
    meeting.value = undefined
    errorMessage.value = getApiErrorMessage(error, '会议入口不存在或尚未发布。')
  }
}

/**
 * 填入本地联调嘉宾示例。
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
 * 调用后端 API 完成嘉宾登录并读取完整个人资料。
 *
 * 入参：
 *   无；函数从页面表单中读取姓名和手机号，两个字段均必填。
 *
 * 返回值：
 *   Promise<void>：登录成功后保存嘉宾会话并跳转到嘉宾会议列表。
 *
 * 异常：
 *   身份不匹配、会议无效或网络异常时展示后端错误提示。
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
  try {
    const result = await loginGuest(meeting.value.id, name.value.trim(), phone.value.trim())
    session.setGuest(result.user, result.access)
    featureMessage.value = ''
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '嘉宾登录失败，请检查姓名和手机号。')
  } finally {
    loading.value = false
  }
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
 * 展开会议功能侧边面板并清除上一次功能提示。
 *
 * 入参：无。
 * 返回值：void：显示右侧会议功能面板。
 * 异常：当前函数不主动抛出异常。
 */
function openFeatureDrawer(): void {
  featureMessage.value = ''
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
  if (!value) {
    return '待定'
  }
  return new Date(value).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}

onMounted(loadMeeting)
</script>
