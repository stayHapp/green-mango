<template>
  <section class="page narrow-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">管理员端</p>
        <h1>管理员登录</h1>
        <p class="muted">使用 mock 数据中的管理员姓名和手机号进入会议管理。</p>
      </div>
      <el-tag type="info">Mock 登录</el-tag>
    </div>

    <el-card shadow="never" class="form-card">
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="姓名">
          <el-input v-model="name" placeholder="请输入管理员姓名" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="phone" placeholder="请输入手机号" />
        </el-form-item>
        <div class="action-row">
          <el-button @click="fillDemoAdmin">填入示例</el-button>
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

import { loginAdmin } from '../../mock/mockApi'
import { useSessionStore } from '../../stores/session'

const router = useRouter()
const session = useSessionStore()
const name = ref('')
const phone = ref('')
const loading = ref(false)
const errorMessage = ref('')

/**
 * 使用 mock 数据填入一组管理员登录示例。
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
function fillDemoAdmin(): void {
  name.value = '周敏'
  phone.value = '13800000001'
  errorMessage.value = ''
}

/**
 * 执行管理员端 mock 登录。
 *
 * 入参：
 *   无；函数从页面表单中读取姓名和手机号，两个字段均必填。
 *
 * 返回值：
 *   Promise<void>：登录成功后保存管理员会话并跳转到会议管理页。
 *
 * 异常：
 *   mock API 当前不主动抛出异常；匹配不到管理员时展示页面错误提示。
 */
async function handleLogin(): Promise<void> {
  errorMessage.value = ''

  if (!name.value.trim() || !phone.value.trim()) {
    errorMessage.value = '请填写姓名和手机号。'
    return
  }

  loading.value = true
  const admin = await loginAdmin(name.value.trim(), phone.value.trim())
  loading.value = false

  if (!admin) {
    errorMessage.value = '未找到匹配的管理员，请检查 mock 登录信息。'
    return
  }

  session.setAdmin(admin)
  router.push('/admin/meetings')
}
</script>
