<template>
  <section class="page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">工作人员端</p>
        <h1>{{ meeting?.title ?? '会议签到' }}</h1>
        <p class="muted">{{ meeting ? `${meeting.location}｜${formatDate(meeting.startTime)}` : '请先选择会议。' }}</p>
      </div>
      <el-button v-if="!session.staff" type="primary" @click="goLogin">去登录</el-button>
    </div>

    <el-empty v-if="!session.staff" description="暂无工作人员会话" />
    <el-empty v-else-if="!meeting" description="未找到会议" />
    <div v-else class="detail-grid">
      <el-card shadow="never" class="form-card">
        <template #header>扫码签到</template>
        <el-form label-position="top" @submit.prevent>
          <el-form-item label="嘉宾二维码 token">
            <el-input v-model="qrToken" placeholder="请输入或粘贴嘉宾 token" />
          </el-form-item>
          <div class="action-row">
            <el-button @click="fillDemoToken">填入示例</el-button>
            <el-button type="primary" :loading="loading" @click="handleScan">确认签到</el-button>
          </div>
        </el-form>
      </el-card>

      <el-card shadow="never">
        <template #header>签到结果</template>
        <el-empty v-if="!scanResult" description="等待扫码" />
        <div v-else>
          <el-alert :type="resultAlertType" :closable="false" :title="scanResult.message" />
          <dl v-if="scanResult.guest" class="info-list top-gap">
            <dt>嘉宾</dt>
            <dd>{{ scanResult.guest.name }}</dd>
            <dt>单位</dt>
            <dd>{{ scanResult.guest.organization }}</dd>
            <dt>座位</dt>
            <dd>{{ scanResult.guest.seat }}</dd>
          </dl>
        </div>
      </el-card>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getMeeting, scanGuest } from '../../mock/mockApi'
import { useSessionStore } from '../../stores/session'
import type { Meeting, ScanResult } from '../../types'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const qrToken = ref('')
const loading = ref(false)
const scanResult = ref<ScanResult>()
const resultAlertType = computed(alertType)

/**
 * 加载工作人员签到页的会议详情。
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
 * 根据扫码状态计算 Element Plus 提示类型。
 *
 * 入参：
 *   无；函数读取当前扫码结果状态。
 *
 * 返回值：
 *   'success' | 'warning' | 'error' | 'info'：适用于 el-alert 的类型。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function alertType(): 'success' | 'warning' | 'error' | 'info' {
  if (!scanResult.value) {
    return 'info'
  }

  if (scanResult.value.status === 'success') {
    return 'success'
  }

  if (scanResult.value.status === 'already_checked_in') {
    return 'warning'
  }

  return 'error'
}

/**
 * 填入 mock 数据中的嘉宾二维码 token 示例。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：只更新当前 token 输入框。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function fillDemoToken(): void {
  qrToken.value = 'QR-MEDU-G002'
}

/**
 * 执行 mock 扫码签到。
 *
 * 入参：
 *   无；函数从路由读取会议 ID，从会话读取工作人员 ID，从表单读取二维码 token。
 *
 * 返回值：
 *   Promise<void>：签到完成后更新页面扫码结果。
 *
 * 异常：
 *   当前 mock API 不主动抛出异常；缺少工作人员会话或 token 时展示错误结果。
 */
async function handleScan(): Promise<void> {
  if (!session.staff) {
    scanResult.value = { status: 'invalid', message: '请先完成工作人员登录。' }
    return
  }

  if (!qrToken.value.trim()) {
    scanResult.value = { status: 'invalid', message: '请填写嘉宾二维码 token。' }
    return
  }

  loading.value = true
  scanResult.value = await scanGuest(String(route.params.id), session.staff.id, qrToken.value.trim())
  loading.value = false
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
