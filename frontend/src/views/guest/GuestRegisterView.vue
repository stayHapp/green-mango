<template>
  <section class="guest-register-page">
    <div class="guest-home-shell">
      <main class="guest-register-content">
        <router-link class="guest-page-back-link" :to="`/meetings/${meetingId}`">
          <el-icon><ArrowLeft /></el-icon>
          返回活动首页
        </router-link>

        <div v-if="loading && !meeting" v-loading="loading" class="page-loading-block guest-entry-loading" />

        <div v-else-if="loadError" class="guest-home-error">
          <el-alert type="error" :closable="false" :title="loadError" />
          <el-button type="primary" plain @click="loadMeeting">重新加载</el-button>
        </div>

        <template v-else-if="meeting">
          <GuestMeetingSummary :meeting="meeting" />

          <section v-if="submitted" class="guest-register-success" aria-live="polite">
            <span class="guest-register-success__icon"><el-icon><CircleCheckFilled /></el-icon></span>
            <p class="guest-entry-eyebrow">提交成功</p>
            <h1>报名申请已进入审核</h1>
            <p>会务人员审核通过后，你可以使用本次填写的姓名和手机号登录，查看个人入场码与会议服务。</p>
            <div class="guest-register-success__actions">
              <el-button type="primary" @click="openLogin">前往参会登录</el-button>
              <router-link :to="`/meetings/${meetingId}`">返回活动首页</router-link>
            </div>
          </section>

          <el-card v-else shadow="never" class="guest-register-card">
            <template #header>
              <div>
                <strong>申请报名</strong>
                <p>请填写真实参会信息，提交后由会务人员审核</p>
              </div>
            </template>

            <el-alert
              v-if="!meeting.registrationEnabled"
              type="info"
              :closable="false"
              title="当前会议暂未开放自主报名。"
            />

            <el-form v-else label-position="top" class="guest-register-form" @submit.prevent="handleSubmit">
              <el-form-item label="姓名" required :error="nameError">
                <el-input ref="nameInput" v-model="form.name" autocomplete="name" placeholder="请输入姓名" @input="clearNameError" />
              </el-form-item>
              <el-form-item label="手机号" required :error="phoneError">
                <el-input
                  ref="phoneInput"
                  v-model="form.phone"
                  autocomplete="tel"
                  inputmode="tel"
                  placeholder="用于审核通过后的参会登录"
                  @input="clearPhoneError"
                />
              </el-form-item>
              <el-form-item label="单位">
                <el-input v-model="form.organization" autocomplete="organization" placeholder="请输入单位名称（选填）" @input="clearSubmitError" />
              </el-form-item>
              <el-form-item label="职务">
                <el-input v-model="form.title" placeholder="请输入职务（选填）" @input="clearSubmitError" />
              </el-form-item>
              <el-alert v-if="submitError" class="guest-login-form-error" type="error" :closable="false" :title="submitError" />
              <p class="guest-register-privacy">提交即表示你同意会务人员仅将这些信息用于本次会议报名审核与现场服务。</p>
              <el-button class="guest-register-submit" type="primary" native-type="submit" :loading="submitting">提交报名申请</el-button>
            </el-form>
          </el-card>
        </template>
      </main>
    </div>
  </section>
</template>

<script setup lang="ts">
import { nextTick, onMounted, reactive, ref } from 'vue'
import type { InputInstance } from 'element-plus'
import { ArrowLeft, CircleCheckFilled } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'

import { getApiErrorMessage } from '../../api/client'
import { submitGuestApplication } from '../../api/guestApplications'
import { getPublicMeeting } from '../../api/sessions'
import GuestMeetingSummary from '../../components/GuestMeetingSummary.vue'
import type { GuestApplicationInput, Meeting } from '../../types'

const route = useRoute()
const router = useRouter()
const meetingId = route.params.id ? String(route.params.id) : ''
const meeting = ref<Meeting>()
const loading = ref(false)
const submitting = ref(false)
const submitted = ref(false)
const loadError = ref('')
const submitError = ref('')
const nameError = ref('')
const phoneError = ref('')
const nameInput = ref<InputInstance>()
const phoneInput = ref<InputInstance>()
const form = reactive<GuestApplicationInput>({ name: '', phone: '', organization: '', title: '' })

/**
 * 加载报名页需要展示的公开会议信息和报名开关。
 *
 * 入参：无；函数读取当前路由会议 ID。
 * 返回值：Promise<void>：成功后更新会议内容和页面状态。
 * 异常：会议不存在、尚未发布或网络失败时捕获异常并展示中文提示。
 */
async function loadMeeting(): Promise<void> {
  loadError.value = ''
  if (!meetingId) {
    loadError.value = '缺少会议入口 ID，无法提交报名申请。'
    return
  }
  loading.value = true
  try {
    meeting.value = await getPublicMeeting(meetingId)
  } catch (error) {
    meeting.value = undefined
    loadError.value = getApiErrorMessage(error, '会议入口不存在或尚未发布。')
  } finally {
    loading.value = false
  }
}

/**
 * 清除姓名字段和本次提交的全局错误。
 *
 * 入参：无；由姓名输入事件触发。
 * 返回值：void：清空姓名错误与提交错误。
 * 异常：当前函数不主动抛出异常。
 */
function clearNameError(): void {
  nameError.value = ''
  submitError.value = ''
}

/**
 * 清除手机号字段和本次提交的全局错误。
 *
 * 入参：无；由手机号输入事件触发。
 * 返回值：void：清空手机号错误与提交错误。
 * 异常：当前函数不主动抛出异常。
 */
function clearPhoneError(): void {
  phoneError.value = ''
  submitError.value = ''
}

/**
 * 清除服务端返回的报名提交错误。
 *
 * 入参：无；由可选字段输入事件触发。
 * 返回值：void：清空提交错误。
 * 异常：当前函数不主动抛出异常。
 */
function clearSubmitError(): void {
  submitError.value = ''
}

/**
 * 校验报名必填字段并聚焦第一个缺失输入框。
 *
 * 入参：无；函数读取当前报名表单。
 * 返回值：Promise<boolean>：姓名和手机号均非空时返回 true，否则返回 false。
 * 异常：当前函数不主动抛出异常。
 */
async function validateForm(): Promise<boolean> {
  nameError.value = form.name.trim() ? '' : '请输入姓名'
  phoneError.value = form.phone.trim() ? '' : '请输入手机号'
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
 * 向当前会议提交公开报名申请并展示待审核结果。
 *
 * 入参：无；函数读取当前会议、报名开关和表单内容。
 * 返回值：Promise<void>：提交成功后切换到成功状态。
 * 异常：重复申请、会议关闭报名、字段无效或网络失败时捕获异常并展示中文提示。
 */
async function handleSubmit(): Promise<void> {
  submitError.value = ''
  if (!meeting.value?.registrationEnabled) {
    submitError.value = '当前会议暂未开放自主报名。'
    return
  }
  if (!(await validateForm())) {
    return
  }
  submitting.value = true
  try {
    await submitGuestApplication(meetingId, {
      name: form.name.trim(),
      phone: form.phone.trim(),
      organization: form.organization?.trim(),
      title: form.title?.trim(),
    })
    submitted.value = true
  } catch (error) {
    submitError.value = getApiErrorMessage(error, '报名提交失败，请检查填写内容后重试。')
  } finally {
    submitting.value = false
  }
}

/**
 * 从报名成功页进入当前会议的嘉宾身份核验页面。
 *
 * 入参：无；函数读取当前会议 ID。
 * 返回值：Promise<void>：完成嘉宾登录页路由跳转。
 * 异常：路由导航失败时由 Vue Router 抛出异常。
 */
async function openLogin(): Promise<void> {
  await router.push({ path: '/guest/login', query: { meetingId } })
}

onMounted(loadMeeting)
</script>
