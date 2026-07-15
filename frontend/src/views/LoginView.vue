<template>
  <section class="page narrow-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">管理与签到入口</p>
        <h1>管理员 / 工作人员登录</h1>
        <p class="muted">管理员管理会议，工作人员进入现场签到工作台；嘉宾请使用会议专属入口登录。</p>
      </div>
      <el-tag type="success">API 登录</el-tag>
    </div>

    <el-card shadow="never" class="form-card">
      <el-tabs v-model="loginRole" stretch>
        <el-tab-pane label="管理员" name="admin">
          <el-form label-position="top" @submit.prevent>
            <el-form-item label="账号"><el-input v-model="adminUsername" autocomplete="username" placeholder="请输入管理员账号" /></el-form-item>
            <el-form-item label="密码"><el-input v-model="adminPassword" autocomplete="current-password" placeholder="请输入密码" show-password type="password" @keyup.enter="handleAdminLogin" /></el-form-item>
            <div class="action-row"><el-button @click="fillAdminDemo">填入示例</el-button><el-button type="primary" :loading="loading" @click="handleAdminLogin">登录管理端</el-button></div>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="工作人员" name="staff">
          <el-form label-position="top" @submit.prevent>
            <el-form-item label="账号"><el-input v-model="staffUsername" autocomplete="username" placeholder="请输入工作人员账号" /></el-form-item>
            <el-form-item label="密码"><el-input v-model="staffPassword" autocomplete="current-password" placeholder="请输入密码" show-password type="password" @keyup.enter="handleStaffLogin" /></el-form-item>
            <div class="action-row"><el-button @click="fillStaffDemo">填入示例</el-button><el-button type="primary" :loading="loading" @click="handleStaffLogin">进入签到工作台</el-button></div>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <el-alert v-if="errorMessage" class="top-gap" type="error" :closable="false" :title="errorMessage" />
    </el-card>

    <p class="muted login-switch-tip">嘉宾请通过会议入口二维码，或前往 <router-link class="inline-link" to="/guest/login">嘉宾登录</router-link>。</p>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { getApiErrorMessage } from '../api/client'
import { loginAdmin, loginStaff } from '../api/sessions'
import { useSessionStore } from '../stores/session'

const router = useRouter()
const session = useSessionStore()
const loginRole = ref<'admin' | 'staff'>('admin')
const adminUsername = ref('')
const adminPassword = ref('')
const staffUsername = ref('')
const staffPassword = ref('')
const loading = ref(false)
const errorMessage = ref('')

/**
 * 切换登录身份时清除上一次的错误提示。
 *
 * 入参：role 为当前选择的登录身份，可取 admin 或 staff。
 * 返回值：void：只更新错误提示状态。
 * 异常：当前函数不主动抛出异常。
 */
function resetErrorOnRoleChange(role: 'admin' | 'staff'): void {
  if (role) {
    errorMessage.value = ''
  }
}

watch(loginRole, resetErrorOnRoleChange)

/**
 * 填入本地联调管理员账号示例。
 *
 * 入参：无。
 * 返回值：void：更新管理员登录表单。
 * 异常：当前函数不主动抛出异常。
 */
function fillAdminDemo(): void {
  adminUsername.value = 'admin'
  adminPassword.value = 'admin-pass-123'
  errorMessage.value = ''
}

/**
 * 填入本地联调工作人员账号示例。
 *
 * 入参：无。
 * 返回值：void：更新工作人员登录表单。
 * 异常：当前函数不主动抛出异常。
 */
function fillStaffDemo(): void {
  staffUsername.value = 'staff01'
  staffPassword.value = 'staff-pass-123'
  errorMessage.value = ''
}

/**
 * 调用后端 API 完成管理员登录并进入会议管理页。
 *
 * 入参：无；函数读取管理员账号与密码表单。
 * 返回值：Promise<void>：登录成功后保存管理员会话并跳转。
 * 异常：字段缺失、凭据错误或网络异常时展示错误提示。
 */
async function handleAdminLogin(): Promise<void> {
  errorMessage.value = ''
  if (!adminUsername.value.trim() || !adminPassword.value) {
    errorMessage.value = '请填写管理员账号和密码。'
    return
  }

  loading.value = true
  try {
    const result = await loginAdmin(adminUsername.value.trim(), adminPassword.value)
    session.setAdmin(result.user, result.access)
    await router.push('/admin/meetings')
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '管理员登录失败，请检查账号和密码。')
  } finally {
    loading.value = false
  }
}

/**
 * 调用后端 API 完成工作人员登录并进入负责会议列表。
 *
 * 入参：无；函数读取工作人员账号与密码表单。
 * 返回值：Promise<void>：登录成功后保存工作人员会话并跳转。
 * 异常：字段缺失、凭据错误或网络异常时展示错误提示。
 */
async function handleStaffLogin(): Promise<void> {
  errorMessage.value = ''
  if (!staffUsername.value.trim() || !staffPassword.value) {
    errorMessage.value = '请填写工作人员账号和密码。'
    return
  }

  loading.value = true
  try {
    const result = await loginStaff(staffUsername.value.trim(), staffPassword.value)
    session.setStaff(result.user, result.access)
    await router.push('/staff/meetings')
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '工作人员登录失败，请检查账号和密码。')
  } finally {
    loading.value = false
  }
}
</script>
