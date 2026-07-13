<template>
  <section class="page narrow-page">
    <div v-if="meeting" class="guest-meeting-hero">
      <div>
        <p class="eyebrow">统一登录</p>
        <h1>{{ meeting.title }}</h1>
        <p class="lead">{{ meeting.description }}</p>
        <dl class="compact-info-list">
          <dt>时间</dt>
          <dd>{{ formatDate(meeting.startTime) }} - {{ formatDate(meeting.endTime) }}</dd>
          <dt>地点</dt>
          <dd>{{ meeting.location }}</dd>
        </dl>
      </div>
      <el-tag type="success">会议入口</el-tag>
    </div>

    <div v-else class="page-heading">
      <div>
        <p class="eyebrow">统一登录</p>
        <h1>知会登录</h1>
        <p class="muted">使用姓名和手机号识别身份，登录后进入对应客户端。</p>
      </div>
      <el-tag type="info">Mock 登录</el-tag>
    </div>

    <el-card shadow="never" class="form-card">
      <template #header>身份验证</template>
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="姓名">
          <el-input v-model="name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="phone" placeholder="请输入手机号" />
        </el-form-item>
        <div class="example-grid">
          <el-button @click="fillAdminDemo">管理员示例</el-button>
          <el-button @click="fillStaffDemo">工作人员示例</el-button>
          <el-button @click="fillGuestDemo">嘉宾示例</el-button>
        </div>
        <div class="action-row top-gap">
          <el-button type="primary" :loading="loading" @click="handleLogin">登录</el-button>
        </div>
      </el-form>
      <el-alert v-if="errorMessage" class="top-gap" type="error" :closable="false" :title="errorMessage" />
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getMeeting, loginByIdentity } from '../mock/mockApi'
import { useSessionStore } from '../stores/session'
import type { IdentityLoginResult, Meeting } from '../types'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const name = ref('')
const phone = ref('')
const loading = ref(false)
const errorMessage = ref('')

/**
 * 加载统一登录页关联的会议信息。
 *
 * 入参：
 *   无；函数从 URL 查询参数读取 meetingId，存在时展示该会议基础信息。
 *
 * 返回值：
 *   Promise<void>：加载完成后更新页面会议展示信息。
 *
 * 异常：
 *   当前 mock API 不主动抛出异常；会议不存在时不展示会议信息。
 */
async function loadMeeting(): Promise<void> {
  if (!route.query.meetingId) {
    meeting.value = undefined
    return
  }

  meeting.value = await getMeeting(String(route.query.meetingId))
}

/**
 * 填入管理员登录示例。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：只更新登录表单。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function fillAdminDemo(): void {
  name.value = '周敏'
  phone.value = '13800000001'
  errorMessage.value = ''
}

/**
 * 填入工作人员登录示例。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：只更新登录表单。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function fillStaffDemo(): void {
  name.value = '现场一组'
  phone.value = '13700000001'
  errorMessage.value = ''
}

/**
 * 填入嘉宾登录示例。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：只更新登录表单。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function fillGuestDemo(): void {
  name.value = '李文博'
  phone.value = '13900000001'
  errorMessage.value = ''
}

/**
 * 执行统一身份登录。
 *
 * 入参：
 *   无；函数从页面表单读取姓名和手机号，两个字段均必填。
 *
 * 返回值：
 *   Promise<void>：登录成功后根据身份进入管理员端、工作人员端或嘉宾端。
 *
 * 异常：
 *   mock API 当前不主动抛出异常；匹配不到身份或会议不匹配时展示页面错误提示。
 */
async function handleLogin(): Promise<void> {
  errorMessage.value = ''

  if (!name.value.trim() || !phone.value.trim()) {
    errorMessage.value = '请填写姓名和手机号。'
    return
  }

  loading.value = true
  const result = await loginByIdentity(name.value.trim(), phone.value.trim())
  loading.value = false

  if (!result) {
    errorMessage.value = '未找到匹配身份，请检查姓名和手机号。'
    return
  }

  enterClient(result)
}

/**
 * 根据统一登录结果进入对应客户端。
 *
 * 入参：
 *   result：统一登录结果，必填，包含身份类型和用户对象。
 *
 * 返回值：
 *   void：保存会话后跳转到对应客户端页面。
 *
 * 异常：
 *   当前函数不主动抛出异常；嘉宾会议入口不匹配时展示页面错误提示。
 */
function enterClient(result: IdentityLoginResult): void {
  if (result.role === 'admin') {
    session.setAdmin(result.user)
    router.push('/admin/meetings')
    return
  }

  if (result.role === 'staff') {
    session.setStaff(result.user)
    router.push('/staff/meetings')
    return
  }

  if (meeting.value && result.user.meetingId !== meeting.value.id) {
    errorMessage.value = '当前嘉宾不属于该会议，请核对入口二维码。'
    return
  }

  session.setGuest(result.user)
  router.push(`/guest/meetings/${result.user.meetingId}`)
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
