<template>
  <section class="page narrow-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">管理与签到入口</p>
        <h1>管理员 / 工作人员登录</h1>
        <p class="muted">管理员管理会议，工作人员进入现场签到工作台；嘉宾请使用会议专属入口登录。</p>
      </div>
      <el-tag type="info">Mock 登录</el-tag>
    </div>

    <el-card shadow="never" class="form-card">
      <el-tabs v-model="loginRole" stretch>
        <el-tab-pane label="管理员" name="admin">
          <el-form label-position="top" @submit.prevent>
            <el-form-item label="姓名"><el-input v-model="adminName" placeholder="请输入管理员姓名" /></el-form-item>
            <el-form-item label="手机号"><el-input v-model="adminPhone" placeholder="请输入手机号" /></el-form-item>
            <div class="action-row"><el-button @click="fillAdminDemo">填入示例</el-button><el-button type="primary" :loading="loading" @click="handleAdminLogin">登录管理端</el-button></div>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="工作人员" name="staff">
          <el-form label-position="top" @submit.prevent>
            <el-form-item label="账号"><el-input v-model="staffAccount" placeholder="请输入工作人员账号" /></el-form-item>
            <div class="action-row"><el-button @click="fillStaffDemo">填入示例</el-button><el-button type="primary" :loading="loading" @click="handleStaffLogin">进入签到工作台</el-button></div>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <el-alert v-if="errorMessage" class="top-gap" type="error" :closable="false" :title="errorMessage" />
    </el-card>

    <p class="muted login-switch-tip">嘉宾请通过会议入口二维码，或前往 <router-link class="inline-link" to="/guest/login?meetingId=m-edu-2026">嘉宾登录</router-link>。</p>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { loginAdmin, loginStaff } from '../mock/mockApi'
import { useSessionStore } from '../stores/session'

const router = useRouter()
const session = useSessionStore()
const loginRole = ref<'admin' | 'staff'>('admin')
const adminName = ref('')
const adminPhone = ref('')
const staffAccount = ref('')
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
 * 填入管理员 Mock 登录示例。
 *
 * 入参：无。
 * 返回值：void：更新管理员登录表单。
 * 异常：当前函数不主动抛出异常。
 */
function fillAdminDemo(): void {
  adminName.value = '周敏'
  adminPhone.value = '13800000001'
  errorMessage.value = ''
}

/**
 * 填入工作人员 Mock 登录示例。
 *
 * 入参：无。
 * 返回值：void：更新工作人员登录表单。
 * 异常：当前函数不主动抛出异常。
 */
function fillStaffDemo(): void {
  staffAccount.value = 'staff01'
  errorMessage.value = ''
}

/**
 * 完成管理员 Mock 登录并进入会议管理页。
 *
 * 入参：无；函数读取管理员姓名与手机号表单。
 * 返回值：Promise<void>：登录成功后保存管理员会话并跳转。
 * 异常：字段缺失或身份未匹配时展示错误提示。
 */
async function handleAdminLogin(): Promise<void> {
  errorMessage.value = ''
  if (!adminName.value.trim() || !adminPhone.value.trim()) {
    errorMessage.value = '请填写管理员姓名和手机号。'
    return
  }

  loading.value = true
  const admin = await loginAdmin(adminName.value.trim(), adminPhone.value.trim())
  loading.value = false
  if (!admin) {
    errorMessage.value = '未找到匹配的管理员，请检查登录信息。'
    return
  }

  session.setAdmin(admin)
  router.push('/admin/meetings')
}

/**
 * 完成工作人员 Mock 登录并进入负责会议列表。
 *
 * 入参：无；函数读取工作人员账号表单。
 * 返回值：Promise<void>：登录成功后保存工作人员会话并跳转。
 * 异常：字段缺失或账号未匹配时展示错误提示。
 */
async function handleStaffLogin(): Promise<void> {
  errorMessage.value = ''
  if (!staffAccount.value.trim()) {
    errorMessage.value = '请填写工作人员账号。'
    return
  }

  loading.value = true
  const staff = await loginStaff(staffAccount.value.trim())
  loading.value = false
  if (!staff) {
    errorMessage.value = '未找到匹配的工作人员账号。'
    return
  }

  session.setStaff(staff)
  router.push('/staff/meetings')
}
</script>
