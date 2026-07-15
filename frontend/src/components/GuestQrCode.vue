<template>
  <div class="guest-qr-code">
    <img v-if="imageUrl" :src="imageUrl" alt="嘉宾签到二维码" class="guest-qr-code__image" />
    <el-alert v-else-if="errorMessage" type="error" :closable="false" :title="errorMessage" />
    <el-skeleton v-else animated>
      <template #template><el-skeleton-item variant="image" class="guest-qr-code__placeholder" /></template>
    </el-skeleton>
    <p class="guest-qr-code__hint">请向工作人员出示此二维码完成签到</p>
  </div>
</template>

<script setup lang="ts">
import QRCode from 'qrcode'
import { ref, watch } from 'vue'

const props = defineProps<{ token: string }>()
const imageUrl = ref('')
const errorMessage = ref('')

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

watch(() => props.token, generateQrCode, { immediate: true })
</script>
