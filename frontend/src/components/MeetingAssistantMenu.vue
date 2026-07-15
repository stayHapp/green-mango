<template>
  <div>
    <div class="feature-drawer-list">
      <button v-for="item in features" :key="item.key" class="feature-menu-item" type="button" @click="openFeature(item)">
        <span class="feature-menu-title">{{ item.title }}</span>
        <span class="feature-menu-desc">{{ item.description }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

import { meetingAssistantFeatureDefinitions } from '../api/meetingAssistant'
import type { MeetingAssistantFeature } from '../types'

const props = defineProps<{ meetingId: string }>()
const router = useRouter()
const features = meetingAssistantFeatureDefinitions

/**
 * 打开嘉宾选择的会议助手功能。
 *
 * 入参：feature 为被点击的功能配置，必填。
 * 返回值：Promise<void>：跳转到对应功能的独立详情页。
 * 异常：当前函数不主动抛出异常。
 */
async function openFeature(feature: Pick<MeetingAssistantFeature, 'key'>): Promise<void> {
  await router.push(`/guest/meetings/${props.meetingId}/assistant/${feature.key}`)
}

</script>
