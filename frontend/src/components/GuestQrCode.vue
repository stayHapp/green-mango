<template>
  <div
    class="guest-qr-code"
    :class="{
      'is-checked-in': isCheckedIn,
      'is-expired': isExpired,
      'is-compact': compact,
      'is-awaiting-check-in': !isCheckedIn && !isExpired && !errorMessage,
    }"
  >
    <div v-if="!compact || isCheckedIn || isExpired || errorMessage" class="guest-qr-code__status">
      <span v-if="compact && isCheckedIn" class="guest-qr-code__status-icon">✓</span>
      <span v-else-if="!compact">{{ statusEyebrow }}</span>
      <strong>{{ statusTitle }}</strong>
      <small v-if="checkedInTime">签到时间：{{ checkedInTime }}</small>
    </div>

    <div v-if="isExpired" class="guest-qr-code__expired-panel">
      <strong>签到已结束</strong>
      <span>会议已结束，个人签到二维码不再有效。</span>
    </div>

    <div v-else-if="!compact || !isCheckedIn" class="guest-qr-code__frame">
      <template v-if="imageUrl">
        <img :src="imageUrl" alt="嘉宾签到二维码" class="guest-qr-code__image" />
        <div v-if="isCheckedIn" class="guest-qr-code__checked-mark" aria-label="已签到">
          <strong>✓ 已签到</strong>
        </div>
      </template>
      <div v-else-if="errorMessage" class="guest-qr-code__error">
        <el-alert type="error" :closable="false" :title="errorMessage" />
        <el-button type="primary" plain @click="loadQrStatus">重新加载</el-button>
      </div>
      <el-skeleton v-else animated>
        <template #template><el-skeleton-item variant="image" class="guest-qr-code__placeholder" /></template>
      </el-skeleton>
    </div>

    <p v-if="!compact || !isCheckedIn || errorMessage" class="guest-qr-code__hint">{{ statusHint }}</p>
  </div>
</template>

<script setup lang="ts">
import QRCode from 'qrcode'
import { computed, ref, watch } from 'vue'

import { getApiErrorMessage } from '../api/client'
import { getGuestCheckInQr } from '../api/sessions'

const props = withDefaults(defineProps<{ meetingId: string; token: string; compact?: boolean }>(), {
  compact: false,
})
const imageUrl = ref('')
const errorMessage = ref('')
const isCheckedIn = ref(false)
const checkedInAt = ref('')
const expiresAt = ref('')
const checkedInTime = computed(formatCheckedInTime)
const isExpired = computed(checkQrExpired)
const statusEyebrow = computed(buildStatusEyebrow)
const statusTitle = computed(buildStatusTitle)
const statusHint = computed(buildStatusHint)

/**
 * 将嘉宾签到 token 生成为可扫描的二维码图像。
 *
 * 入参：token 为嘉宾在当前会议中的随机签到凭证，必填。
 * 返回值：Promise<void>：生成成功后更新二维码数据地址，失败时更新错误提示。
 * 异常：二维码编码库拒绝无效内容或浏览器内存不足时捕获异常并展示提示。
 */
async function generateQrCode(token: string): Promise<void> {
  imageUrl.value = ''
  errorMessage.value = ''
  if (!token) {
    errorMessage.value = '当前嘉宾缺少签到二维码凭证。'
    return
  }

  try {
    imageUrl.value = await QRCode.toDataURL(token, { width: 240, margin: 1, errorCorrectionLevel: 'M' })
  } catch {
    errorMessage.value = '二维码生成失败，请刷新页面后重试。'
  }
}

/**
 * 从服务端加载当前会议的二维码、签到状态和有效期。
 *
 * 入参：无；函数读取组件传入的会议 ID 和本地二维码 token 兜底值。
 * 返回值：Promise<void>：成功后更新二维码、已签到状态、签到时间和过期状态。
 * 异常：会话、权限或网络异常时捕获错误并转换为组件内中文提示。
 */
async function loadQrStatus(): Promise<void> {
  imageUrl.value = ''
  errorMessage.value = ''
  isCheckedIn.value = false
  checkedInAt.value = ''
  expiresAt.value = ''
  try {
    const status = await getGuestCheckInQr(props.meetingId)
    isCheckedIn.value = status.isCheckedIn
    checkedInAt.value = status.checkedInAt
    expiresAt.value = status.expiresAt
    // 会议结束后不再生成可操作二维码，服务端仍负责最终有效期校验。
    if (!checkQrExpired()) {
      await generateQrCode(status.qrToken || props.token)
    }
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '签到二维码加载失败，请稍后重试。')
  }
}

/**
 * 判断签到二维码是否已超过服务端返回的有效期。
 *
 * 入参：无；函数读取 expiresAt 响应字段。
 * 返回值：boolean：有效期存在且当前时间已超过时返回 true，否则返回 false。
 * 异常：非法时间文本按未过期处理，最终有效性仍由服务端判断。
 */
function checkQrExpired(): boolean {
  if (!expiresAt.value) {
    return false
  }
  const expiresDate = new Date(expiresAt.value)
  if (Number.isNaN(expiresDate.getTime())) {
    return false
  }
  return Date.now() > expiresDate.getTime()
}

/**
 * 格式化服务端返回的签到时间。
 *
 * 入参：无；函数读取 checkedInAt 签到时间。
 * 返回值：string：有效时间的本地年月日时分文本，无签到时间或时间非法时返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
function formatCheckedInTime(): string {
  if (!checkedInAt.value) {
    return ''
  }
  const date = new Date(checkedInAt.value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

/**
 * 生成签到状态上方的辅助标签。
 *
 * 入参：无；函数读取签到、过期和错误状态。
 * 返回值：string：当前状态对应的简短辅助标签。
 * 异常：当前函数不主动抛出异常。
 */
function buildStatusEyebrow(): string {
  if (isExpired.value) return '会议状态'
  if (errorMessage.value) return '签到凭证'
  return isCheckedIn.value ? '签到成功' : '当前状态'
}

/**
 * 生成签到区域的主要状态标题。
 *
 * 入参：无；函数读取签到、过期和错误状态。
 * 返回值：string：已签到、未签到、签到已结束或凭证暂不可用。
 * 异常：当前函数不主动抛出异常。
 */
function buildStatusTitle(): string {
  if (isExpired.value) return '签到已结束'
  if (errorMessage.value) return '凭证暂不可用'
  return isCheckedIn.value ? '已签到' : '未签到'
}

/**
 * 生成签到状态下方的下一步操作提示。
 *
 * 入参：无；函数读取签到、过期和错误状态。
 * 返回值：string：当前状态对应的操作说明。
 * 异常：当前函数不主动抛出异常。
 */
function buildStatusHint(): string {
  if (isExpired.value) return '如需核验历史签到情况，请联系会务人员。'
  if (errorMessage.value) return '请重新加载；仍无法使用时请联系会务人员。'
  if (isCheckedIn.value) return '签到已完成，无需重复扫码。'
  return '请向工作人员出示此二维码完成签到。'
}

watch(() => [props.meetingId, props.token], loadQrStatus, { immediate: true })
</script>
