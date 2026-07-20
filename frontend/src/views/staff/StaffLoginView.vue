<template>
  <section class="staff-login-page">
    <main class="staff-login-panel">
      <router-link class="staff-login-back" :to="`/meetings/${meetingId}`">
        <el-icon><ArrowLeft /></el-icon>
        返回首页
      </router-link>

      <div class="staff-login-icon" aria-hidden="true">
        <el-icon><Postcard /></el-icon>
      </div>
      <h1>工作人员登录</h1>
      <p>登录后进行现场签到</p>

      <el-alert
        v-if="errorMessage"
        class="staff-login-alert"
        type="error"
        :closable="false"
        :title="errorMessage"
      />

      <el-form class="staff-login-form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="username"
            autocomplete="username"
            placeholder="账号"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="password"
            autocomplete="current-password"
            placeholder="密码"
            :prefix-icon="Lock"
            show-password
            type="password"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-button
          class="staff-login-submit"
          native-type="submit"
          type="primary"
          :loading="loading"
        >
          登录
        </el-button>
      </el-form>
    </main>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowLeft, Lock, Postcard, User } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

import { getApiErrorMessage } from '../../api/client'
import { loginStaff } from '../../api/sessions'
import { listStaffMeetings } from '../../api/staffCheckIns'
import { useSessionStore } from '../../stores/session'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')
const meetingId = computed(readMeetingId)

/**
 * 从会议专属工作人员登录路由读取会议 ID。
 *
 * 入参：无；函数读取当前路由参数 `id`。
 * 返回值：string：会议 ID 字符串，缺失时返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
function readMeetingId(): string {
  return route.params.id ? String(route.params.id) : ''
}

/**
 * 登录工作人员账号、校验当前会议授权并直达签到工作台。
 *
 * 入参：无；函数读取当前会议 ID、账号和密码表单。
 * 返回值：Promise<void>：授权成功后保存会话并完成签到工作台跳转。
 * 异常：字段缺失、凭据错误、会议未授权或网络异常时转换为页面错误提示。
 */
async function handleLogin(): Promise<void> {
  errorMessage.value = ''
  if (!meetingId.value) {
    errorMessage.value = '缺少会议入口，请从会议首页进入工作人员端。'
    return
  }
  if (!username.value.trim() || !password.value) {
    errorMessage.value = '请输入账号和密码。'
    return
  }

  loading.value = true
  try {
    const result = await loginStaff(username.value.trim(), password.value)
    session.setStaff(result.user, result.access)
    const authorizedMeetings = await listStaffMeetings()
    const hasCurrentMeeting = authorizedMeetings.some((meeting) => meeting.id === meetingId.value)
    if (!hasCurrentMeeting) {
      session.clearStaff()
      errorMessage.value = '当前账号未被授权负责本会议。'
      return
    }
    await router.replace(`/staff/meetings/${meetingId.value}/check-in`)
  } catch (error) {
    session.clearStaff()
    errorMessage.value = getApiErrorMessage(error, '工作人员登录失败，请检查账号和密码。')
  } finally {
    loading.value = false
  }
}
</script>
