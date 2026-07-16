<template>
  <MeetingAssistantShortcutGrid :meeting-id="meetingId" />
</template>

<script setup lang="ts">
import MeetingAssistantShortcutGrid from './MeetingAssistantShortcutGrid.vue'

defineProps<{ meetingId: string }>()
</script>
