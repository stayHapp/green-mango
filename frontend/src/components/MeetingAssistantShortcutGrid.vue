<template>
  <div class="assistant-shortcut-grid">
    <button
      v-for="item in shortcutItems"
      :key="item.key"
      type="button"
      class="assistant-shortcut-item"
      :aria-label="item.title"
      @click="openFeature(item.key)"
    >
      <span class="assistant-shortcut-item__icon">
        <el-icon><component :is="item.icon" /></el-icon>
      </span>
      <span class="assistant-shortcut-item__label">{{ item.shortTitle }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Component } from 'vue'
import { Calendar, Location, PhoneFilled, Reading, Sunny } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

import { meetingAssistantFeatureDefinitions } from '../api/meetingAssistant'
import type { MeetingAssistantFeatureKey } from '../types'

interface AssistantShortcutItem {
  key: MeetingAssistantFeatureKey
  title: string
  shortTitle: string
  icon: Component
}

const props = defineProps<{ meetingId: string }>()
const emit = defineEmits<{ select: [key: MeetingAssistantFeatureKey] }>()
const router = useRouter()
const shortTitles: Record<MeetingAssistantFeatureKey, string> = {
  agenda: '日程',
  manual: '手册',
  weather: '天气',
  route: '路线',
  contact: '联系',
}
const icons: Record<MeetingAssistantFeatureKey, Component> = {
  agenda: Calendar,
  manual: Reading,
  weather: Sunny,
  route: Location,
  contact: PhoneFilled,
}
const shortcutItems: AssistantShortcutItem[] = meetingAssistantFeatureDefinitions.map((item) => ({
  key: item.key,
  title: item.title,
  shortTitle: shortTitles[item.key],
  icon: icons[item.key],
}))

/**
 * 打开选中的会议助手功能，并通知外层收起快捷入口。
 *
 * 入参：key 为固定会议助手功能标识，必填。
 * 返回值：Promise<void>：路由跳转完成后结束。
 * 异常：路由导航失败时由 Vue Router 抛出异常。
 */
async function openFeature(key: MeetingAssistantFeatureKey): Promise<void> {
  emit('select', key)
  await router.push(`/guest/meetings/${props.meetingId}/assistant/${key}`)
}
</script>
