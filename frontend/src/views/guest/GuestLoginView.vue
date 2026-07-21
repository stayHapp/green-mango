<template>
  <section class="page guest-portal-page guest-login-page">
    <div class="phone-wrapper guest-login-wrapper" v-loading="loading && !meeting">
      <router-link v-if="meetingId" class="guest-page-back-link" :to="`/meetings/${meetingId}`">
        <el-icon><ArrowLeft /></el-icon>
        返回首页
      </router-link>
      <header class="guest-login-heading">
        <h1>参会登录</h1>
        <p>请输入报名时使用的姓名与手机号，查看您的专属入场码</p>
      </header>
      <div v-if="!meeting && !loading" class="guest-entry-error">
        <el-empty description="未找到会议入口" />
        <el-alert v-if="errorMessage" type="error" :closable="false" :title="errorMessage" />
      </div>

      <div v-if="meeting" class="guest-login-panel">
        <el-form class="guest-login-form" label-position="top" @submit.prevent="handleLogin">
          <el-form-item label="姓名" :error="nameError">
            <el-input
              ref="nameInput"
              v-model="name"
              autocomplete="name"
              placeholder="请输入姓名"
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
              <svg class="guest-login-submit__icon" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M14 8l4 4-4 4M18 12H7M10 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h5" />
              </svg>
              登录
            </el-button>
          </div>
        </el-form>
        <p class="guest-login-register-tip">
          <span>还没有报名？</span>
          <router-link :to="`/meetings/${meetingId}/register`">立即报名</router-link>
        </p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import type { InputInstance } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

import { getApiErrorMessage } from '../../api/client'
import { getPublicMeeting, loginGuest } from '../../api/sessions'
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
const meetingId = route.query.meetingId ? String(route.query.meetingId) : ''

/**
 * 加载会议专属入口信息，并将已有的同会议嘉宾会话直接送回当前会议首页。
 *
 * 入参：无；函数读取 URL 中的 meetingId 查询参数。
 * 返回值：Promise<void>：成功后展示登录信息，或跳转至会话所属的当前会议首页。
 * 异常：会议不存在、尚未发布或网络不可用时捕获异常并展示中文提示。
 */
async function loadMeeting(): Promise<void> {
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

<style scoped>
.guest-login-page {
  min-height: 100dvh;
  background: #f6f8f7;
}

.guest-login-page::before {
  display: none;
}

.guest-login-wrapper {
  display: block;
  min-height: 100dvh;
  padding: 22px 24px 52px;
  background: #f6f8f7;
  box-shadow: none;
}

.guest-page-back-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #63766f;
  font-size: 15px;
  font-weight: 500;
  line-height: 24px;
}

.guest-page-back-link :deep(.el-icon) {
  font-size: 18px;
}

.guest-login-heading {
  display: block;
  justify-items: stretch;
  margin: 48px 0 34px;
  text-align: left;
}

.guest-login-heading h1 {
  margin: 0;
  color: #10251e;
  font-family: inherit;
  font-size: 30px;
  font-weight: 760;
  line-height: 1.3;
  letter-spacing: -0.02em;
}

.guest-login-heading p {
  max-width: none;
  margin: 12px 0 0;
  color: #667a72;
  font-family: inherit;
  font-size: 14px;
  font-weight: 400;
  line-height: 1.65;
}

.guest-login-panel {
  width: 100%;
}

.guest-login-form :deep(.el-form-item) {
  margin-bottom: 22px;
}

.guest-login-form :deep(.el-form-item__label) {
  height: auto;
  margin-bottom: 7px;
  padding: 0;
  color: #526a61;
  font-size: 14px;
  font-weight: 560;
  line-height: 1.5;
}

.guest-login-form :deep(.el-input__wrapper) {
  min-height: 54px;
  border: 1px solid #dbe3df;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: none;
  padding: 0 17px;
  transition: border-color 160ms ease, box-shadow 160ms ease;
}

.guest-login-form :deep(.el-input__wrapper:hover) {
  border-color: #b8c7c0;
}

.guest-login-form :deep(.el-input__wrapper.is-focus) {
  border-color: #00513b;
  box-shadow: 0 0 0 3px rgba(0, 81, 59, 0.09);
}

.guest-login-form :deep(.el-input__inner) {
  color: #19352d;
  font-size: 16px;
}

.guest-login-form :deep(.el-input__inner::placeholder) {
  color: #b5c0bb;
}

.guest-login-primary-action {
  padding-top: 1px;
}

.guest-login-submit.el-button {
  min-height: 52px;
  border: 0;
  border-radius: 16px;
  background: #00513b;
  box-shadow: none;
  color: #ffffff;
  font-size: 16px;
  font-weight: 650;
  letter-spacing: 0.02em;
}

.guest-login-submit.el-button:hover,
.guest-login-submit.el-button:focus-visible {
  background: #003f2f;
}

.guest-login-submit__icon {
  width: 20px;
  height: 20px;
  margin-right: 7px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 2;
}

.guest-login-register-tip {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin: 25px 0 0;
  color: #718079;
  font-size: 14px;
  line-height: 1.6;
}

.guest-login-register-tip a {
  color: #00513b;
  font-weight: 560;
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 4px;
}

.guest-login-form-error {
  margin: -6px 0 14px;
}

@media (max-width: 380px) {
  .guest-login-wrapper {
    padding-right: 20px;
    padding-left: 20px;
  }

  .guest-login-heading {
    margin-top: 40px;
  }
}
</style>
