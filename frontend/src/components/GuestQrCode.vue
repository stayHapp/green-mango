<template>
  <div class="guest-qr-code">
    <div class="guest-qr-code__frame">
      <template v-if="imageUrl">
        <img :src="imageUrl" alt="嘉宾签到二维码" class="guest-qr-code__image" />
        <div v-if="isCheckedIn" class="guest-qr-code__checked-mark" aria-label="已签到">
          <strong>✓ 已签到</strong>
          <span v-if="checkedInTime">{{ checkedInTime }}</span>
        </div>
      </template>
      <el-alert v-else-if="errorMessage" type="error" :closable="false" :title="errorMessage" />
      <el-skeleton v-else animated>
        <template #template><el-skeleton-item variant="image" class="guest-qr-code__placeholder" /></template>
      </el-skeleton>
    </div>
    <p class="guest-qr-code__hint">{{ isCheckedIn ? '签到已完成，无需重复扫码' : '请向工作人员出示此二维码完成签到' }}</p>
  </div>
</template>

<script setup lang="ts">
import QRCode from 'qrcode'
import { computed, ref, watch } from 'vue'

import { getApiErrorMessage } from '../api/client'
import { getGuestCheckInQr } from '../api/sessions'

const props = defineProps<{ meetingId: string; token: string }>()
const imageUrl = ref('')
const errorMessage = ref('')
const isCheckedIn = ref(false)
const checkedInAt = ref('')
const checkedInTime = computed(formatCheckedInTime)

/**
 * 将嘉宾签到 token 生成为可扫描的二维码图像。
 *
 * 入参：token 为嘉宾在当前会议中的签到凭证，必填。
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
 * 从服务端加载二维码及签到状态，再生成当前二维码图像。
 *
 * 入参：无；函数读取组件的会议 ID 和本地二维码 token 兜底值。
 * 返回值：Promise<void>：成功后更新二维码、“已签到”标记和签到时间。
 * 异常：会话、权限或网络异常时转换为组件内错误提示。
 */
async function loadQrStatus(): Promise<void> {
  imageUrl.value = ''
  errorMessage.value = ''
  isCheckedIn.value = false
  checkedInAt.value = ''
  try {
    const status = await getGuestCheckInQr(props.meetingId)
    isCheckedIn.value = status.isCheckedIn
    checkedInAt.value = status.checkedInAt
    await generateQrCode(status.qrToken || props.token)
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '签到二维码加载失败，请刷新页面后重试。')
  }
}

/**
 * 格式化二维码标记中的签到时间。
 *
 * 入参：无；函数读取服务端返回的签到时间。
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

watch(() => [props.meetingId, props.token], loadQrStatus, { immediate: true })
</script>
