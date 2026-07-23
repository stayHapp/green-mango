<script setup lang="ts">
/**
 * 兼容旧入口 `/login`，与 `/admin/login` 共用同一套 PC 管理后台登录页。
 */
import AdminLoginView from './admin/AdminLoginView.vue'
</script>

<template>
  <AdminLoginView />
</template>
