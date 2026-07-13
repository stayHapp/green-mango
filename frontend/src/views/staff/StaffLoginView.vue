<template>
  <section class="page narrow-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">工作人员端</p>
        <h1>工作人员登录</h1>
        <p class="muted">使用 mock 账号进入签到工作台。</p>
      </div>
      <el-tag type="info">Mock 登录</el-tag>
    </div>

    <el-card shadow="never" class="form-card">
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="账号">
          <el-input v-model="account" placeholder="请输入工作人员账号" />
        </el-form-item>
        <div class="action-row">
          <el-button @click="fillDemoStaff">填入示例</el-button>
          <el-button type="primary" :loading="loading" @click="handleLogin">登录</el-button>
        </div>
      </el-form>
      <el-alert v-if="errorMessage" class="top-gap" type="error" :closable="false" :title="errorMessage" />
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { loginStaff } from '../../mock/mockApi'
import { useSessionStore } from '../../stores/session'

const router = useRouter()
const session = useSessionStore()
const account = ref('')
const loading = ref(false)
const errorMessage = ref('')

/**
 * 使用 mock 数据填入工作人员登录示例。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：只更新当前表单字段。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function fillDemoStaff(): void {
  account.value = 'staff01'
  errorMessage.value = ''
}

/**
 * 执行工作人员端 mock 登录。
 *
 * 入参：
 *   无；函数从页面表单中读取账号，账号必填。
 *
 * 返回值：
 *   Promise<void>：登录成功后保存工作人员会话并跳转到负责会议列表。
 *
 * 异常：
 *   mock API 当前不主动抛出异常；匹配不到账号时展示页面错误提示。
 */
async function handleLogin(): Promise<void> {
  errorMessage.value = ''

  if (!account.value.trim()) {
    errorMessage.value = '请填写工作人员账号。'
    return
  }

  loading.value = true
  const staff = await loginStaff(account.value.trim())
  loading.value = false

  if (!staff) {
    errorMessage.value = '未找到匹配的工作人员账号。'
    return
  }

  session.setStaff(staff)
  router.push('/staff/meetings')
}
</script>
