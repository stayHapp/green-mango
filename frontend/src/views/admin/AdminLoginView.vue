<template>
  <section class="admin-login-page">
    <div class="admin-login-card">
      <aside class="admin-login-brand" aria-hidden="true">
        <div class="admin-login-brand__deco-ring" />
        <div class="admin-login-brand__deco-dot" />

        <div class="admin-login-brand__logo">
          <div class="admin-login-brand__mark">知</div>
          <div class="admin-login-brand__name">知会</div>
        </div>

        <div class="admin-login-brand__slogan">
          <h2>智能会议服务</h2>
          <p>嘉宾 · 工作人员 · 会议管理<br />一站式会议签到与信息管理平台</p>
        </div>

        <div class="admin-login-brand__footer">
          <span>知会 · 后台管理</span>
          <span>v0.1.0</span>
        </div>
      </aside>

      <main class="admin-login-form-pane">
        <div class="admin-login-form-inner">
          <div class="admin-login-form-eyebrow">后台管理</div>
          <h1>欢迎回来</h1>
          <p class="admin-login-form-sub">请使用管理员账号登录</p>

          <div v-if="errorMessage" class="admin-login-error" role="alert">{{ errorMessage }}</div>

          <form class="admin-login-form" @submit.prevent="handleLogin">
            <div class="admin-login-field">
              <label for="admin-account">账号</label>
              <div class="admin-login-input-wrap">
                <input
                  id="admin-account"
                  v-model="username"
                  type="text"
                  autocomplete="username"
                  placeholder="请输入管理员账号"
                  @input="errorMessage = ''"
                />
              </div>
            </div>

            <div class="admin-login-field">
              <label for="admin-password">密码</label>
              <div class="admin-login-input-wrap">
                <input
                  id="admin-password"
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="current-password"
                  placeholder="请输入密码"
                  @input="errorMessage = ''"
                />
                <button
                  type="button"
                  class="admin-login-eye"
                  :aria-label="showPassword ? '隐藏密码' : '显示密码'"
                  @click="showPassword = !showPassword"
                >
                  <el-icon :size="18">
                    <View v-if="showPassword" />
                    <Hide v-else />
                  </el-icon>
                </button>
              </div>
            </div>

            <div class="admin-login-form-row">
              <label class="admin-login-remember">
                <input v-model="rememberMe" type="checkbox" />
                记住我
              </label>
              <button type="button" class="admin-login-link" @click="showForgotHint">忘记密码？</button>
            </div>

            <button type="submit" class="admin-login-submit" :disabled="loading">
              <span v-if="loading" class="admin-login-spinner" aria-hidden="true" />
              <span>{{ loading ? '正在登录' : '登 录 管 理 后 台' }}</span>
            </button>

            <button type="button" class="admin-login-fill" @click="fillDemo">填入示例账号（开发环境）</button>
          </form>
        </div>
      </main>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Hide, View } from '@element-plus/icons-vue'

import { getApiErrorMessage } from '../../api/client'
import { loginAdmin } from '../../api/sessions'
import { useSessionStore } from '../../stores/session'

const REMEMBER_USERNAME_KEY = 'green-mango-admin-remember-username'

const router = useRouter()
const session = useSessionStore()
const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')

/**
 * 页面加载时读取“记住我”保存的管理员账号。
 */
onMounted(() => {
  try {
    const saved = window.localStorage.getItem(REMEMBER_USERNAME_KEY)
    if (saved) {
      username.value = saved
      rememberMe.value = true
    }
  } catch {
    // 本地存储不可用时忽略，不影响登录。
  }
})

/**
 * 填入本地联调管理员账号示例。
 */
function fillDemo(): void {
  username.value = 'admin'
  password.value = 'admin-pass-123'
  errorMessage.value = ''
}

/**
 * 提示忘记密码时的处理方式。
 */
function showForgotHint(): void {
  ElMessage.info('请联系会议组织方重置管理员密码。')
}

/**
 * 调用后端 API 完成管理员登录并进入会议管理页。
 */
async function handleLogin(): Promise<void> {
  errorMessage.value = ''
  const account = username.value.trim()
  if (!account) {
    errorMessage.value = '请输入管理员账号'
    return
  }
  if (!password.value) {
    errorMessage.value = '请输入密码'
    return
  }

  loading.value = true
  try {
    const result = await loginAdmin(account, password.value)
    session.setAdmin(result.user, result.access)
    try {
      if (rememberMe.value) {
        window.localStorage.setItem(REMEMBER_USERNAME_KEY, account)
      } else {
        window.localStorage.removeItem(REMEMBER_USERNAME_KEY)
      }
    } catch {
      // 本地存储失败不影响登录成功流程。
    }
    await router.push('/admin/meetings')
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '账号或密码不正确，请重新输入')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.admin-login-page {
  --green-deep: #1a3a2e;
  --green-mid: #2d5a4a;
  --green-brand: #3d6f5c;
  --green-brand-dark: #2f5747;
  --text-title: #203a2e;
  --text-sub: #6c7d74;
  --bg-page: #eef2f0;
  --bg-right: #f7f9f8;
  --error: #d64545;

  box-sizing: border-box;
  width: 100%;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 20px; 

  background: var(--bg-page);
  color: var(--text-title);
  font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans SC", "Helvetica Neue", Arial, sans-serif;
}

.admin-login-card {
  width: 100%;
  max-width: 980px;
  min-height: 600px;
  display: flex;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(26, 58, 46, 0.16), 0 4px 16px rgba(26, 58, 46, 0.08);
  background: #fff;
}

.admin-login-brand {
  flex: 0 0 40%;
  position: relative;
  background: linear-gradient(150deg, var(--green-deep) 0%, var(--green-mid) 100%);
  color: #fff;
  padding: 56px 44px 36px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.admin-login-brand::before {
  content: "";
  position: absolute;
  width: 340px;
  height: 340px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0) 68%);
  top: -110px;
  right: -110px;
}

.admin-login-brand::after {
  content: "";
  position: absolute;
  width: 260px;
  height: 260px;
  border-radius: 50%;
  border: 1.5px solid rgba(255, 255, 255, 0.14);
  bottom: -80px;
  left: -70px;
}

.admin-login-brand__deco-ring {
  position: absolute;
  width: 120px;
  height: 120px;
  border-radius: 28px;
  border: 1.5px solid rgba(255, 255, 255, 0.12);
  transform: rotate(24deg);
  top: 46%;
  right: -40px;
}

.admin-login-brand__deco-dot {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.35);
  top: 30%;
  right: 24%;
}

.admin-login-brand__logo {
  display: flex;
  align-items: center;
  gap: 14px;
  position: relative;
  z-index: 1;
}

.admin-login-brand__mark {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.28);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
  backdrop-filter: blur(2px);
}

.admin-login-brand__name {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 6px;
}

.admin-login-brand__slogan {
  position: relative;
  z-index: 1;
  margin-top: auto;
}

.admin-login-brand__slogan h2 {
  font-size: 24px;
  font-weight: 600;
  letter-spacing: 2px;
  margin-bottom: 14px;
}

.admin-login-brand__slogan p {
  font-size: 14px;
  line-height: 2;
  color: rgba(255, 255, 255, 0.72);
  letter-spacing: 1px;
}

.admin-login-brand__footer {
  position: relative;
  z-index: 1;
  margin-top: 44px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.16);
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 1px;
  display: flex;
  justify-content: space-between;
}

.admin-login-form-pane {
  flex: 1;
  background: var(--bg-right);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
}

.admin-login-form-inner {
  width: 100%;
  max-width: 380px;
}

.admin-login-form-eyebrow {
  font-size: 13px;
  font-weight: 600;
  color: var(--green-brand);
  letter-spacing: 2px;
  margin-bottom: 10px;
}

.admin-login-form-inner h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-title);
  margin: 0 0 8px;
}

.admin-login-form-sub {
  font-size: 14px;
  color: var(--text-sub);
  margin: 0 0 32px;
}

.admin-login-field {
  margin-bottom: 18px;
}

.admin-login-field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-title);
  margin-bottom: 8px;
}

.admin-login-input-wrap {
  position: relative;
}

.admin-login-input-wrap input {
  width: 100%;
  height: 50px;
  padding: 0 46px 0 16px;
  font-size: 15px;
  color: var(--text-title);
  background: #fff;
  border: 1.5px solid #dde5e1;
  border-radius: 12px;
  outline: none;
  transition: border-color 0.18s, box-shadow 0.18s;
}

.admin-login-input-wrap input:hover {
  border-color: #b9c9c1;
}

.admin-login-input-wrap input:focus {
  border-color: var(--green-brand);
  box-shadow: 0 0 0 3px rgba(61, 111, 92, 0.14);
}

.admin-login-input-wrap input::placeholder {
  color: #a9b6b0;
}

.admin-login-eye {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 34px;
  height: 34px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #8fa39a;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}

.admin-login-eye:hover {
  color: var(--green-brand);
  background: rgba(61, 111, 92, 0.08);
}

.admin-login-form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 4px 0 22px;
  font-size: 13px;
}

.admin-login-remember {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-sub);
  cursor: pointer;
  user-select: none;
}

.admin-login-remember input {
  width: 16px;
  height: 16px;
  accent-color: var(--green-brand);
  cursor: pointer;
}

.admin-login-link {
  border: none;
  background: transparent;
  color: var(--green-brand);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.admin-login-link:hover {
  text-decoration: underline;
}

.admin-login-error {
  font-size: 13px;
  color: var(--error);
  background: rgba(214, 69, 69, 0.07);
  border: 1px solid rgba(214, 69, 69, 0.22);
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 16px;
}

.admin-login-submit {
  width: 100%;
  height: 52px;
  border: none;
  border-radius: 12px;
  background: var(--green-brand);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 6px;
  cursor: pointer;
  transition: background 0.18s, transform 0.12s, box-shadow 0.18s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.admin-login-submit:hover:not(:disabled) {
  background: var(--green-brand-dark);
  box-shadow: 0 8px 20px rgba(61, 111, 92, 0.28);
}

.admin-login-submit:active:not(:disabled) {
  transform: translateY(1px);
}

.admin-login-submit:disabled {
  opacity: 0.75;
  cursor: not-allowed;
}

.admin-login-spinner {
  width: 18px;
  height: 18px;
  border: 2.5px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: admin-login-spin 0.7s linear infinite;
}

@keyframes admin-login-spin {
  to {
    transform: rotate(360deg);
  }
}

.admin-login-fill {
  width: 100%;
  margin-top: 12px;
  height: 40px;
  border: 1.5px dashed #c4d2cb;
  border-radius: 12px;
  background: transparent;
  color: var(--text-sub);
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.18s, color 0.18s, background 0.18s;
}

.admin-login-fill:hover {
  border-color: var(--green-brand);
  color: var(--green-brand);
  background: rgba(61, 111, 92, 0.05);
}

@media (max-width: 768px) {
  .admin-login-page {
    padding: 0;
    align-items: stretch;
  }

  .admin-login-card {
    min-height: 100vh;
    min-height: 100dvh;
    border-radius: 0;
    flex-direction: column;
  }

  .admin-login-brand {
    flex: none;
    padding: 32px 28px;
  }

  .admin-login-brand__slogan {
    margin-top: 24px;
  }

  .admin-login-brand__slogan h2 {
    font-size: 19px;
  }

  .admin-login-brand__footer {
    margin-top: 24px;
  }

  .admin-login-form-pane {
    flex: 1;
    padding: 36px 24px;
  }
}
</style>
