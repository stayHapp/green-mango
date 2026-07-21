<template>
  <section class="login-portal staff-login-portal">
    <div class="login-portal__card staff-login-portal__card">
      <header class="login-portal__header">
        <div class="login-portal__brand" aria-hidden="true">
          <span>知</span>
          <small>知 会</small>
        </div>
        <h1>管理员登录</h1>
        <p>登录后可创建会议、配置嘉宾字段、维护会议服务和查看签到情况。</p>
      </header>

      <el-form label-position="top" class="login-portal__form" @submit.prevent>
        <el-form-item label="账号">
          <el-input
            v-model="username"
            autocomplete="username"
            placeholder="请输入管理员账号"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="password"
            autocomplete="current-password"
            placeholder="请输入密码"
            show-password
            type="password"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <div class="login-portal__actions">
          <el-button @click="fillDemo">填入示例</el-button>
          <el-button type="primary" :loading="loading" @click="handleLogin">
            登录管理端
          </el-button>
        </div>
      </el-form>

      <el-alert
        v-if="errorMessage"
        class="login-portal__alert"
        type="error"
        :closable="false"
        :title="errorMessage"
      />

      <footer class="login-portal__footer">
        <p>
          嘉宾和工作人员请通过会议专属入口进入，账号问题请联系会议组织方。
        </p>
      </footer>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { getApiErrorMessage } from '../../api/client'
import { loginAdmin } from '../../api/sessions'
import { useSessionStore } from '../../stores/session'

const router = useRouter()
const session = useSessionStore()
const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

/**
 * 填入本地联调管理员账号示例。
 *
 * 入参：无。
 * 返回值：void：更新管理员登录表单。
 * 异常：当前函数不主动抛出异常。
 */
function fillDemo(): void {
  username.value = 'admin'
  password.value = 'admin-pass-123'
  errorMessage.value = ''
}

/**
 * 调用后端 API 完成管理员登录并进入会议管理页。
 *
 * 入参：无；函数读取账号与密码表单。
 * 返回值：Promise<void>：登录成功后保存管理员会话并跳转。
 * 异常：字段缺失、凭据错误或网络异常时展示错误提示。
 */
async function handleLogin(): Promise<void> {
  errorMessage.value = ''
  if (!username.value.trim() || !password.value) {
    errorMessage.value = '请填写管理员账号和密码。'
    return
  }

  loading.value = true
  try {
    const result = await loginAdmin(username.value.trim(), password.value)
    session.setAdmin(result.user, result.access)
    await router.push('/admin/meetings')
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '管理员登录失败，请检查账号和密码。')
  } finally {
    loading.value = false
  }
}
</script>
