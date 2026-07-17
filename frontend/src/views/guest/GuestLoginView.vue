<template>
  <section class="page guest-portal-page">
    <div class="phone-wrapper guest-login-wrapper">
      <GuestMeetingSummary v-if="meeting" :meeting="meeting" />
      <div v-else-if="!loading" class="guest-entry-error">
        <el-empty description="未找到会议入口" />
        <el-alert v-if="errorMessage" type="error" :closable="false" :title="errorMessage" />
      </div>

      <el-card v-if="meeting" shadow="never" class="form-card guest-login-card">
        <template #header>
          <div>
            <strong>嘉宾身份核验</strong>
            <p>请输入报名时填写的姓名和手机号</p>
          </div>
        </template>
        <el-form class="guest-login-form" label-position="top" @submit.prevent="handleLogin">
          <el-form-item label="姓名" :error="nameError">
            <el-input
              ref="nameInput"
              v-model="name"
              autocomplete="name"
              placeholder="请输入嘉宾姓名"
              @input="clearNameError"
            />
          </el-form-item>
          <el-form-item label="手机号" :error="phoneError">
            <el-input
              ref="phoneInput"
              v-model="phone"
              autocomplete="tel"
              inputmode="tel"
              placeholder="请输入手机号"
              @input="clearPhoneError"
            />
          </el-form-item>
          <el-alert
            v-if="errorMessage"
            class="guest-login-form-error"
            type="error"
            :closable="false"
            :title="errorMessage"
          />
          <div class="guest-login-primary-action">
            <el-button class="guest-login-submit" type="primary" native-type="submit" :loading="loading">
              进入当前会议
            </el-button>
          </div>
        </el-form>
      </el-card>
    </div>
  </section>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import type { InputInstance } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import { getApiErrorMessage } from '../../api/client'
import { getPublicMeeting, loginGuest } from '../../api/sessions'
import GuestMeetingSummary from '../../components/GuestMeetingSummary.vue'
import { useSessionStore } from '../../stores/session'
import type { Meeting } from '../../types'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const name = ref('')
const phone = ref('')
const nameInput = ref<InputInstance>()
const phoneInput = ref<InputInstance>()
const nameError = ref('')
const phoneError = ref('')
const loading = ref(false)
const errorMessage = ref('')

/**
 * 加载会议专属入口信息，并将已有的同会议嘉宾会话直接送回当前会议首页。
 *
 * 入参：无；函数读取 URL 中的 meetingId 查询参数。
 * 返回值：Promise<void>：成功后展示登录信息，或跳转至会话所属的当前会议首页。
 * 异常：会议不存在、尚未发布或网络不可用时捕获异常并展示中文提示。
 */
async function loadMeeting(): Promise<void> {
  const meetingId = route.query.meetingId ? String(route.query.meetingId) : ''
  errorMessage.value = ''

  if (!meetingId) {
    errorMessage.value = '缺少会议入口 ID，请通过会议专属二维码进入。'
    return
  }

  loading.value = true
  try {
    meeting.value = await getPublicMeeting(meetingId)
    // 嘉宾身份只属于当前会议，已有同会议会话时不重复展示登录表单。
    if (session.guest?.meetingId === meetingId) {
      await router.replace(`/guest/meetings/${meetingId}`)
    }
  } catch (error) {
    meeting.value = undefined
    errorMessage.value = getApiErrorMessage(error, '会议入口不存在或尚未发布。')
  } finally {
    loading.value = false
  }
}

/**
 * 清除姓名字段和服务端身份核验错误，允许用户重新输入。
 *
 * 入参：无；由姓名输入事件触发。
 * 返回值：void：清空姓名字段错误与全局核验错误。
 * 异常：当前函数不主动抛出异常。
 */
function clearNameError(): void {
  nameError.value = ''
  errorMessage.value = ''
}

/**
 * 清除手机号字段和服务端身份核验错误，允许用户重新输入。
 *
 * 入参：无；由手机号输入事件触发。
 * 返回值：void：清空手机号字段错误与全局核验错误。
 * 异常：当前函数不主动抛出异常。
 */
function clearPhoneError(): void {
  phoneError.value = ''
  errorMessage.value = ''
}

/**
 * 校验身份核验表单，并聚焦第一个缺失字段。
 *
 * 入参：无；函数读取姓名和手机号输入值。
 * 返回值：Promise<boolean>：两个字段均有有效非空文本时返回 true，否则返回 false。
 * 异常：当前函数不主动抛出异常。
 */
async function validateLoginForm(): Promise<boolean> {
  nameError.value = name.value.trim() ? '' : '请输入报名时填写的姓名'
  phoneError.value = phone.value.trim() ? '' : '请输入报名时填写的手机号'

  if (!nameError.value && !phoneError.value) {
    return true
  }

  await nextTick()
  if (nameError.value) {
    nameInput.value?.focus()
  } else {
    phoneInput.value?.focus()
  }
  return false
}

/**
 * 核验当前会议内的嘉宾身份，并进入唯一的当前会议首页。
 *
 * 入参：无；函数读取会议、姓名和手机号表单值，三者均必填。
 * 返回值：Promise<void>：登录成功后保存嘉宾会话并替换为当前会议详情路由。
 * 异常：身份不匹配、会议无效或网络异常时捕获错误并展示中文提示。
 */
async function handleLogin(): Promise<void> {
  errorMessage.value = ''

  if (!meeting.value) {
    errorMessage.value = '当前会议入口无效，无法核验身份。'
    return
  }

  if (!(await validateLoginForm())) {
    return
  }

  loading.value = true
  try {
    const result = await loginGuest(meeting.value.id, name.value.trim(), phone.value.trim())
    session.setGuest(result.user, result.access)
    await router.replace(`/guest/meetings/${meeting.value.id}`)
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '身份核验失败，请检查姓名和手机号。')
  } finally {
    loading.value = false
  }
}

onMounted(loadMeeting)
</script>
