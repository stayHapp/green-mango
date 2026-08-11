<template>
  <section
    class="guest-home-summary"
    :class="{ 'is-compact': compact, 'has-description': showDescription && meeting.description }"
    aria-labelledby="guest-meeting-title"
  >
    <div v-if="!compact" class="guest-home-summary__brand" aria-label="知会">
      <span>知</span>
      <small>知 会</small>
    </div>
    <h1 id="guest-meeting-title">{{ meeting.title }}</h1>
    <p v-if="showDescription && meeting.description" class="guest-home-summary__description">
      {{ meeting.description }}
    </p>
    <div class="guest-home-summary__meta">
      <div>
        <el-icon><Calendar /></el-icon>
        <strong>{{ formatMeetingRange(meeting.startTime, meeting.endTime, meeting.timeDisplayMode) }}</strong>
      </div>
      <div>
        <el-icon><Location /></el-icon>
        <strong>{{ meeting.location || '待会务确认' }}</strong>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Calendar, Location } from '@element-plus/icons-vue'

import type { Meeting } from '../types'
import { formatMeetingRange } from '../utils/meetingTime'

withDefaults(defineProps<{ meeting: Meeting; compact?: boolean; showDescription?: boolean }>(), {
  compact: false,
  showDescription: false,
})
</script>
