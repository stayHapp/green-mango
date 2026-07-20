<template>
  <div
    class="assistant-shortcut-shell"
    :class="{ 'has-more': canScrollForward, 'is-drawer': props.variant === 'drawer' }"
  >
    <div ref="shortcutScroller" class="assistant-shortcut-grid" @scroll="updateScrollState">
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
        <span class="assistant-shortcut-item__copy">
          <strong>{{ item.title }}</strong>
          <small>{{ item.description }}</small>
        </span>
        <el-icon class="assistant-shortcut-item__arrow"><ArrowRight /></el-icon>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, type Component } from 'vue'
import { ArrowRight, Calendar, Location, PhoneFilled, Reading, Sunny } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

import { meetingAssistantFeatureDefinitions } from '../api/meetingAssistant'
import type { MeetingAssistantFeatureKey } from '../types'

interface AssistantShortcutItem {
  key: MeetingAssistantFeatureKey
  title: string
  description: string
  icon: Component
}

const props = withDefaults(defineProps<{ meetingId: string; variant?: 'default' | 'drawer' }>(), {
  variant: 'default',
})
const emit = defineEmits<{ select: [key: MeetingAssistantFeatureKey] }>()
const router = useRouter()
const shortcutScroller = ref<HTMLElement>()
const canScrollForward = ref(false)
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
  description: item.description,
  icon: icons[item.key],
}))

/**
 * 更新会议服务横向列表是否仍有未显示内容。
 *
 * 入参：无；函数读取快捷服务滚动容器的可视宽度、内容宽度和当前位置。
 * 返回值：void：更新右侧渐变提示的显示状态。
 * 异常：容器尚未挂载时直接结束，不主动抛出异常。
 */
function updateScrollState(): void {
  const scroller = shortcutScroller.value
  if (!scroller) {
    canScrollForward.value = false
    return
  }
  canScrollForward.value = scroller.scrollLeft + scroller.clientWidth < scroller.scrollWidth - 2
}

/**
 * 在窗口尺寸变化后重新计算会议服务列表的可滚动状态。
 *
 * 入参：无；由浏览器 resize 事件触发。
 * 返回值：void：同步更新横向列表提示状态。
 * 异常：当前函数不主动抛出异常。
 */
function handleWindowResize(): void {
  updateScrollState()
}

/**
 * 在组件挂载后初始化横向列表状态和窗口尺寸监听。
 *
 * 入参：无；由 Vue 组件生命周期触发。
 * 返回值：Promise<void>：等待 DOM 更新后完成首次测量和事件绑定。
 * 异常：当前函数不主动抛出异常。
 */
async function initializeShortcutScroller(): Promise<void> {
  await nextTick()
  updateScrollState()
  window.addEventListener('resize', handleWindowResize)
}

/**
 * 在组件卸载前移除窗口尺寸监听，避免残留事件处理器。
 *
 * 入参：无；由 Vue 组件生命周期触发。
 * 返回值：void：完成事件解绑。
 * 异常：当前函数不主动抛出异常。
 */
function disposeShortcutScroller(): void {
  window.removeEventListener('resize', handleWindowResize)
}

/**
 * 打开选中的会议服务，并通知外层完成入口选择。
 *
 * 入参：key 为固定会议助手功能标识，必填。
 * 返回值：Promise<void>：路由跳转完成后结束。
 * 异常：路由导航失败时由 Vue Router 抛出异常。
 */
async function openFeature(key: MeetingAssistantFeatureKey): Promise<void> {
  emit('select', key)
  await router.push(`/guest/meetings/${props.meetingId}/assistant/${key}`)
}

onMounted(initializeShortcutScroller)
onBeforeUnmount(disposeShortcutScroller)
</script>
