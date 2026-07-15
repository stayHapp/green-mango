<template>
  <div v-loading="loading">
    <div class="feature-drawer-list">
      <button v-for="item in features" :key="item.key" class="feature-menu-item" type="button" @click="openFeature(item)">
        <span class="feature-menu-title">{{ item.title }}</span>
        <span class="feature-menu-desc">{{ item.description }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { listMeetingAssistantFeatures } from '../mock/meetingAssistant'
import type { MeetingAssistantFeature } from '../types'

const props = defineProps<{ meetingId: string }>()
const router = useRouter()
const features = ref<MeetingAssistantFeature[]>([])
const loading = ref(false)

/**
 * 加载当前会议的会议助手配置。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<void>：完成后更新五项功能列表并清除旧选择。
 * 异常：当前 Mock 服务不主动抛出异常。
 */
async function loadFeatures(meetingId: string): Promise<void> {
  if (!meetingId) {
    features.value = []
    return
  }
  loading.value = true
  features.value = await listMeetingAssistantFeatures(meetingId)
  loading.value = false
}

/**
 * 打开嘉宾选择的会议助手功能。
 *
 * 入参：feature 为被点击的功能配置，必填。
 * 返回值：Promise<void>：跳转到对应功能的独立详情页。
 * 异常：当前函数不主动抛出异常。
 */
async function openFeature(feature: MeetingAssistantFeature): Promise<void> {
  await router.push(`/guest/meetings/${props.meetingId}/assistant/${feature.key}`)
}

watch(() => props.meetingId, loadFeatures, { immediate: true })
</script>
