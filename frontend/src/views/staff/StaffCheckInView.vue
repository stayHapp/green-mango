<template>
  <section class="staff-workspace-page">
    <header class="staff-workspace-header">
      <div>
        <h1>{{ activeModeTitle }}</h1>
        <p>{{ session.staff?.name || '工作人员' }}</p>
      </div>
      <button type="button" class="staff-workspace-logout" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon>
        退出
      </button>
    </header>

    <main class="staff-workspace-content">
      <el-empty v-if="!session.staff" description="请先登录当前会议工作人员端">
        <el-button type="primary" @click="goLogin">前往登录</el-button>
      </el-empty>
      <el-alert v-else-if="pageError" type="error" :closable="false" :title="pageError" />
      <el-skeleton v-else-if="pageLoading" :rows="8" animated />
      <el-empty v-else-if="!meeting" description="未找到会议" />

      <template v-else>
        <el-alert
          v-if="!isOnline"
          class="staff-network-alert"
          type="error"
          :closable="false"
          title="网络连接已断开，暂时无法完成新的签到操作；请恢复网络后重试。"
        />

        <section class="staff-current-meeting" :aria-label="`${meeting.title}，${currentCheckInSessionTitle}`">
          <h2>{{ meeting.title }}</h2>
          <div class="staff-current-session">
            <strong>{{ currentCheckInSessionTitle }}</strong>
          </div>
        </section>

        <section v-if="activeMode === 'scan'" class="staff-scan-view">
          <div
            class="staff-scan-stage"
            :class="{ 'is-scanning': cameraScanning, 'is-starting': cameraStarting }"
            role="button"
            tabindex="0"
            :aria-label="cameraScanning ? '摄像头已开启，正在连续扫码' : '点击开启摄像头扫码'"
            @click="startCameraScan"
            @keydown.enter.prevent="startCameraScan"
            @keydown.space.prevent="startCameraScan"
          >
            <video
              v-show="cameraScanning"
              id="staff-qr-reader"
              class="staff-scan-camera"
              playsinline
              autoplay
              muted
            />
            <div v-if="!cameraScanning" class="staff-scan-placeholder">
              <el-icon><Camera /></el-icon>
              <span>{{ cameraStarting ? '正在打开摄像头' : '点击扫码区域打开摄像头' }}</span>
            </div>
            <button
              v-if="cameraScanning"
              type="button"
              class="staff-scan-close"
              aria-label="关闭摄像头"
              @click.stop="stopCameraScan"
            >
              <el-icon><Close /></el-icon>
            </button>
            <i class="staff-scan-corner is-top-left" />
            <i class="staff-scan-corner is-top-right" />
            <i class="staff-scan-corner is-bottom-left" />
            <i class="staff-scan-corner is-bottom-right" />
            <i v-if="cameraScanning" class="staff-scan-line" />
            <span v-if="cameraScanning" class="staff-scan-live-dot">连续扫码中</span>
            <div v-if="scanFeedback" class="staff-scan-result-overlay" aria-live="polite" @click.stop>
              <el-alert :type="resultAlertType" :closable="false" :title="scanFeedback.message" />
            </div>
          </div>

          <button type="button" class="staff-manual-link" @click="switchWorkspaceMode('manual')">
            无法扫码？手动签到
          </button>

          <section v-if="latestScannedGuestResult?.duplicate || latestScannedGuestResult?.guest" class="staff-scan-result" aria-live="polite">
            <dl v-if="latestScannedGuestResult.duplicate">
              <div><dt>签到场次</dt><dd>{{ currentCheckInSessionTitle }}</dd></div>
              <div><dt>嘉宾</dt><dd>{{ latestScannedGuestResult.duplicate.guestName }}</dd></div>
              <div><dt>电话</dt><dd>{{ latestScannedGuestResult.duplicate.phone }}</dd></div>
              <div><dt>已签到时间</dt><dd>{{ formatDate(latestScannedGuestResult.duplicate.checkedInAt) }}</dd></div>
              <div><dt>签到方式</dt><dd>{{ methodText(latestScannedGuestResult.duplicate.method) }}</dd></div>
            </dl>
            <dl v-else-if="latestScannedGuestResult.guest">
              <div><dt>签到场次</dt><dd>{{ latestScannedGuestResult.checkIn?.sessionTitle || currentCheckInSessionTitle }}</dd></div>
              <div><dt>嘉宾</dt><dd>{{ latestScannedGuestResult.guest.name }}</dd></div>
              <div><dt>电话</dt><dd>{{ latestScannedGuestResult.guest.phone }}</dd></div>
              <div><dt>签到时间</dt><dd>{{ latestScannedGuestResult.checkIn ? formatDate(latestScannedGuestResult.checkIn.checkedInAt) : '-' }}</dd></div>
            </dl>
          </section>
        </section>

        <section v-else-if="activeMode === 'manual'" class="staff-manual-view">
          <template v-if="selectedManualGuest">
            <article class="staff-confirm-card">
              <div class="staff-confirm-card__identity">
                <span>{{ selectedManualGuest.name.slice(0, 1) }}</span>
                <div>
                  <h2>{{ selectedManualGuest.name }}</h2>
                  <p>{{ selectedManualGuest.phone }}</p>
                  <el-tag :type="selectedManualGuest.checkedIn ? 'success' : 'info'">
                    {{ selectedManualGuest.checkedIn ? '已签到' : '待签到' }}
                  </el-tag>
                </div>
              </div>
              <dl class="staff-confirm-card__details">
                <div v-if="isStaffGuestFieldVisible(selectedManualGuest, 'organization')">
                  <dt>单位</dt>
                  <dd>{{ selectedManualGuest.organization || '未填写' }}</dd>
                </div>
                <div v-if="isStaffGuestFieldVisible(selectedManualGuest, 'tag')">
                  <dt>身份</dt>
                  <dd>{{ selectedManualGuest.tag || '嘉宾' }}</dd>
                </div>
                <div v-if="isStaffGuestFieldVisible(selectedManualGuest, 'seat')">
                  <dt>座位</dt>
                  <dd>{{ selectedManualGuest.seat || '待分配' }}</dd>
                </div>
              </dl>
            </article>
            <div class="staff-confirm-tip">
              <el-icon><InfoFilled /></el-icon>
              请核对嘉宾信息后确认签到
            </div>
            <div class="staff-confirm-actions">
              <el-button @click="clearManualSelection">下一位</el-button>
              <el-button
                type="primary"
                :loading="manualLoadingId === selectedManualGuest.id"
                :disabled="!isOnline || selectedManualGuest.checkedIn"
                @click="confirmManualCheckIn"
              >
                {{ selectedManualGuest.checkedIn ? '已签到' : '确认签到' }}
              </el-button>
            </div>
          </template>

          <template v-else>
            <el-input
              v-model="guestQuery"
              clearable
              class="staff-guest-search"
              :placeholder="staffGuestSearchPlaceholder"
              :prefix-icon="Search"
            />
            <div class="staff-manual-results">
              <el-empty v-if="!filteredGuestRows.length" description="未找到匹配嘉宾" :image-size="72" />
              <article v-for="row in filteredGuestRows" :key="row.id" class="staff-guest-row">
                <span class="staff-guest-row__avatar">{{ row.name.slice(0, 1) }}</span>
                <div class="staff-guest-row__copy">
                  <strong>{{ row.name }}</strong>
                  <p>{{ row.phone }}</p>
                  <small>{{ buildStaffGuestSummary(row) }}</small>
                </div>
                <el-button
                  v-if="!row.checkedIn"
                  type="primary"
                  plain
                  @click="selectManualGuest(row)"
                >
                  核对签到
                </el-button>
                <el-tag v-else type="success">已签到</el-tag>
              </article>
            </div>
          </template>
        </section>

        <section v-else-if="activeMode === 'companions'" class="staff-companions-view">
          <el-input
            v-model="guestQuery"
            clearable
            class="staff-guest-search"
            :placeholder="staffGuestSearchPlaceholder"
            :prefix-icon="Search"
          />
          <el-empty v-if="!displayedGuests.length" description="未找到匹配嘉宾" :image-size="72" />

          <template v-if="companionCheckedRows.length">
            <div class="staff-companions-group">
              <strong>已签到</strong>
              <small>按签到时间倒序 · {{ companionCheckedRows.length }} 位</small>
            </div>
            <article
              v-for="row in companionCheckedRows"
              :key="row.id"
              class="staff-companion-card"
            >
              <span class="staff-companion-card__avatar">{{ row.name.slice(0, 1) }}</span>
              <div class="staff-companion-card__copy">
                <div class="staff-companion-card__head">
                  <strong>{{ row.name }}</strong>
                  <span v-if="row.companionCount > 0" class="staff-companion-card__badge">
                    已带 {{ row.companionCount }} 人
                  </span>
                </div>
                <p>{{ row.phone }}</p>
                <small>{{ buildStaffGuestSummary(row) }}</small>
              </div>
              <div class="staff-companion-card__right">
                <span class="staff-companion-card__time">{{ formatCheckInTime(row.checkedInAt) }}</span>
                <el-button type="primary" plain @click="openCompanionDialog(row)">添加同行</el-button>
              </div>
            </article>
          </template>

          <div class="staff-companions-group">
            <strong>未签到</strong>
            <small>{{ companionUncheckedRows.length }} 位</small>
          </div>
          <article
            v-for="row in companionUncheckedRows"
            :key="row.id"
            class="staff-companion-card"
          >
            <span class="staff-companion-card__avatar is-pending">{{ row.name.slice(0, 1) }}</span>
            <div class="staff-companion-card__copy">
              <div class="staff-companion-card__head">
                <strong>{{ row.name }}</strong>
                <span v-if="row.companionCount > 0" class="staff-companion-card__badge">
                  已带 {{ row.companionCount }} 人
                </span>
              </div>
              <p>{{ row.phone }}</p>
              <small>{{ buildStaffGuestSummary(row) }}</small>
            </div>
            <div class="staff-companion-card__right">
              <span class="staff-companion-card__time is-pending">未签到</span>
              <el-button type="primary" plain @click="openCompanionDialog(row)">添加同行</el-button>
            </div>
          </article>
        </section>

        <section v-else class="staff-records-view">
          <div class="staff-workspace-stats" aria-label="签到统计">
            <div><strong>{{ guests.length }}</strong><span>参会人员</span></div>
            <div><strong>{{ checkedCount }}</strong><span>已签到</span></div>
            <div><strong>{{ uncheckedCount }}</strong><span>未签到</span></div>
          </div>
          <el-empty v-if="!checkInRows.length" description="暂无签到记录" :image-size="72" />
          <article v-for="row in checkInRows" :key="row.id" class="staff-record-row">
            <span>{{ row.guestName.slice(0, 1) }}</span>
            <div>
              <strong>{{ row.guestName }}</strong>
              <p>{{ row.phone }}</p>
              <small>{{ row.sessionTitle }}｜{{ formatDate(row.checkedInAt) }}</small>
            </div>
            <em>{{ methodText(row.method) }}</em>
          </article>
        </section>
      </template>
    </main>

    <!-- 同行人员登记居中弹窗 -->
    <el-dialog
      v-model="companionDialogVisible"
      align-center
      width="88%"
      class="staff-companion-dialog"
      :close-on-click-modal="false"
      @closed="resetCompanionForm"
    >
      <template #header>
        <div class="staff-companion-dialog__header">
          <el-icon><UserFilled /></el-icon>
          <span>添加同行人员</span>
        </div>
      </template>
      <div v-if="companionTarget" class="staff-companion-dialog__primary">
        <span class="staff-companion-dialog__avatar">{{ companionTarget.name.slice(0, 1) }}</span>
        <div class="staff-companion-dialog__identity">
          <strong>{{ companionTarget.name }}</strong>
          <span>{{ companionTarget.phone }}</span>
        </div>
        <span class="staff-companion-dialog__lock">主嘉宾 · 已锁定</span>
      </div>
      <el-form label-position="top" class="staff-companion-dialog__form">
        <el-form-item label="姓名" required>
          <el-input v-model="companionForm.name" placeholder="同行人员姓名" maxlength="100" />
        </el-form-item>
        <el-form-item label="手机号" required>
          <el-input v-model="companionForm.phone" placeholder="同行人员手机号" maxlength="30" />
        </el-form-item>
        <el-form-item label="单位（选填）">
          <el-input v-model="companionForm.organization" placeholder="单位名称" maxlength="255" />
        </el-form-item>
        <el-form-item label="备注（选填）">
          <el-input
            v-model="companionForm.companionNote"
            placeholder="由工作人员自行填写，如：家属、司机"
            maxlength="255"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="companionDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="companionSubmitting"
          :disabled="!isOnline"
          @click="submitCompanion"
        >
          确认登记
        </el-button>
      </template>
    </el-dialog>

    <nav v-if="session.staff && meeting" class="staff-workspace-nav" aria-label="签到工作台导航">
      <button
        v-for="item in workspaceModes"
        :key="item.key"
        type="button"
        :class="{ 'is-active': activeMode === item.key }"
        @click="switchWorkspaceMode(item.key)"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </button>
    </nav>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Camera, Close, InfoFilled, Postcard, Search, SwitchButton, Tickets, UserFilled } from '@element-plus/icons-vue'
import jsQR from 'jsqr'

import { getApiErrorMessage } from '../../api/client'
import { logoutClientSession } from '../../api/sessions'
import {
  createStaffCompanion,
  getAlreadyCheckedInDetail,
  getStaffCheckInSession,
  listStaffCheckIns,
  listStaffMeetings,
  manualStaffCheckIn,
  scanStaffCheckIn,
  searchStaffGuests,
  type CompanionCreatePayload,
  type StaffGuest,
} from '../../api/staffCheckIns'
import { useSessionStore } from '../../stores/session'
import type { CheckInRecord, Meeting, ScanResult, StaffCheckInSession } from '../../types'

interface CheckInRow extends CheckInRecord {
  guestName: string
  phone: string
}

type StaffWorkspaceMode = 'scan' | 'manual' | 'companions' | 'records'

interface StaffWorkspaceModeItem {
  key: StaffWorkspaceMode
  label: string
  icon: Component
}

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const currentCheckInSession = ref<StaffCheckInSession>()
const guests = ref<StaffGuest[]>([])
const displayedGuests = ref<StaffGuest[]>([])
const checkIns = ref<CheckInRecord[]>([])
const qrToken = ref('')
const guestQuery = ref('')
const loading = ref(false)
const manualLoadingId = ref('')
const isOnline = ref(navigator.onLine)
const cameraScanning = ref(false)
const cameraStarting = ref(false)
const pageLoading = ref(false)
const pageError = ref('')
const activeMode = ref<StaffWorkspaceMode>('scan')
const selectedManualGuest = ref<StaffGuest>()
const companionDialogVisible = ref(false)
const companionTarget = ref<StaffGuest>()
const companionSubmitting = ref(false)
const companionForm = ref<CompanionCreatePayload>({
  companionOfId: '',
  name: '',
  phone: '',
  organization: '',
  title: '',
  tag: '',
  seat: '',
  companionNote: '',
})
let guestSearchTimer: number | undefined
let cameraScanGeneration = 0
let scanStream: MediaStream | null = null
let scanAnimationId: number | null = null
let lastCameraToken = ''
let lastCameraTokenAt = 0
let scanFeedbackTimer: number | undefined
const cameraScanCooldownMs = 2000
const sameCameraTokenCooldownMs = 6000
const scanFeedback = ref<ScanResult>()
const latestScannedGuestResult = ref<ScanResult>()
const resultAlertType = computed(alertType)
const activeModeTitle = computed(currentModeTitle)
const staffGuestSearchPlaceholder = computed(buildStaffGuestSearchPlaceholder)
const checkedCount = computed(() => checkIns.value.length)
const uncheckedCount = computed(() => Math.max(guests.value.length - checkedCount.value, 0))
const filteredGuestRows = computed(() => displayedGuests.value)
const companionCheckedRows = computed(() =>
  displayedGuests.value
    .filter((item) => item.checkedIn)
    .sort((a, b) => b.checkedInAt.localeCompare(a.checkedInAt)),
)
const companionUncheckedRows = computed(() => displayedGuests.value.filter((item) => !item.checkedIn))
const currentCheckInSessionTitle = computed(resolveCurrentCheckInSessionTitle)
const checkInRows = computed<CheckInRow[]>(() => checkIns.value.map((record) => {
  const guest = guests.value.find((item) => item.id === record.guestId)
  return {
    ...record,
    guestName: guest?.name ?? '未知嘉宾',
    phone: guest?.phone ?? '-',
  }
}))
const workspaceModes: StaffWorkspaceModeItem[] = [
  { key: 'scan', label: '扫码签到', icon: Camera },
  { key: 'manual', label: '手动签到', icon: Postcard },
  { key: 'companions', label: '同行登记', icon: UserFilled },
  { key: 'records', label: '签到记录', icon: Tickets },
]

/**
 * 解析工作人员端当前签到场次标题。
 *
 * 入参：无；函数优先读取当前场次接口数据，接口异常时回退到最近签到记录中的场次名称。
 * 返回值：string：当前有效签到场次名称，缺失时返回兜底提示。
 * 异常：当前函数不主动抛出异常。
 */
function resolveCurrentCheckInSessionTitle(): string {
  return currentCheckInSession.value?.title || checkIns.value[0]?.sessionTitle || '当前场次'
}

/**
 * 判断工作人员端是否允许展示指定嘉宾字段。
 *
 * 入参：guest 为工作人员端嘉宾或扫码结果嘉宾，可为空；fieldKey 为固定字段标识，必填。
 * 返回值：boolean：后端返回的 visibleFields 包含该字段时返回 true；缺少配置时按兼容模式返回 true。
 * 异常：当前函数不主动抛出异常。
 */
function isStaffGuestFieldVisible(guest: { visibleFields?: string[] } | undefined, fieldKey: string): boolean {
  return guest?.visibleFields ? guest.visibleFields.includes(fieldKey) : true
}

/**
 * 判断当前会议工作人员端搜索是否启用了指定固定字段。
 *
 * 入参：fieldKey 为固定字段标识，必填。
 * 返回值：boolean：已加载嘉宾配置包含该字段时返回 true；没有样本数据时按默认启用处理。
 * 异常：当前函数不主动抛出异常。
 */
function isStaffSearchFieldVisible(fieldKey: string): boolean {
  const sourceGuest = guests.value[0] ?? displayedGuests.value[0]
  return isStaffGuestFieldVisible(sourceGuest, fieldKey)
}

/**
 * 生成工作人员端嘉宾搜索输入框占位提示。
 *
 * 入参：无；函数读取当前会议启用固定字段。
 * 返回值：string：仅包含可搜索字段的中文提示。
 * 异常：当前函数不主动抛出异常。
 */
function buildStaffGuestSearchPlaceholder(): string {
  const labels = ['姓名', '手机号']
  if (isStaffSearchFieldVisible('organization')) {
    labels.push('单位')
  }
  if (isStaffSearchFieldVisible('seat')) {
    labels.push('座位号')
  }
  return `搜索${labels.join('、')}`
}

/**
 * 生成工作人员端嘉宾列表的辅助信息摘要。
 *
 * 入参：guest 为工作人员端嘉宾，必填。
 * 返回值：string：按会议启用字段拼接单位、身份和座位信息；没有可展示扩展信息时返回核验提示。
 * 异常：当前函数不主动抛出异常。
 */
function buildStaffGuestSummary(guest: StaffGuest): string {
  const parts: string[] = []
  if (isStaffGuestFieldVisible(guest, 'organization') && guest.organization) {
    parts.push(guest.organization)
  }
  if (isStaffGuestFieldVisible(guest, 'tag') && guest.tag) {
    parts.push(guest.tag)
  }
  if (isStaffGuestFieldVisible(guest, 'seat')) {
    parts.push(`座位 ${guest.seat || '待分配'}`)
  }
  return parts.length ? parts.join(' · ') : '按姓名和手机号核对'
}

/**
 * 根据当前工作台模式返回页面标题。
 *
 * 入参：无；函数读取 activeMode 当前值。
 * 返回值：string：扫码签到、手动签到或签到记录标题。
 * 异常：当前函数不主动抛出异常。
 */
function currentModeTitle(): string {
  const titleMap: Record<StaffWorkspaceMode, string> = {
    scan: '扫码签到',
    manual: selectedManualGuest.value ? '确认嘉宾' : '手动签到',
    companions: '同行登记',
    records: '签到记录',
  }
  return titleMap[activeMode.value]
}

/**
 * 切换工作人员签到工作台模式，并在离开扫码页时释放摄像头。
 *
 * 入参：mode 为目标模式，必填，可取 scan、manual 或 records。
 * 返回值：Promise<void>：完成必要资源清理后更新当前模式。
 * 异常：摄像头清理异常由 stopCameraScan 内部吸收。
 */
async function switchWorkspaceMode(mode: StaffWorkspaceMode): Promise<void> {
  if (activeMode.value === 'scan' && mode !== 'scan') {
    await stopCameraScan()
  }
  activeMode.value = mode
  if (mode !== 'manual') {
    selectedManualGuest.value = undefined
  }
}

/**
 * 选择手动签到搜索结果，进入嘉宾资料核对状态。
 *
 * 入参：guest 为需要核对的嘉宾，必填。
 * 返回值：void：保存选中嘉宾并更新页面标题。
 * 异常：当前函数不主动抛出异常。
 */
function selectManualGuest(guest: StaffGuest): void {
  selectedManualGuest.value = guest
}

/**
 * 清除当前手动签到嘉宾，返回搜索结果列表。
 *
 * 入参：无。
 * 返回值：void：清空当前选中嘉宾。
 * 异常：当前函数不主动抛出异常。
 */
function clearManualSelection(): void {
  selectedManualGuest.value = undefined
}

/**
 * 打开为指定嘉宾登记同行人员的居中弹窗。
 *
 * 入参：guest 为目标主嘉宾，必填；弹窗内主嘉宾信息由该对象带出并锁定。
 * 返回值：void：初始化登记表单并显示弹窗。
 * 异常：当前函数不主动抛出异常。
 */
function openCompanionDialog(guest: StaffGuest): void {
  companionTarget.value = guest
  companionForm.value = {
    companionOfId: guest.id,
    name: '',
    phone: '',
    organization: '',
    title: '',
    tag: '',
    seat: '',
    companionNote: '',
  }
  companionDialogVisible.value = true
}

/**
 * 关闭同行登记弹窗后清空表单与目标嘉宾。
 *
 * 入参：无。
 * 返回值：void：重置弹窗内部状态，避免下次打开残留旧数据。
 * 异常：当前函数不主动抛出异常。
 */
function resetCompanionForm(): void {
  companionTarget.value = undefined
  companionForm.value = {
    companionOfId: '',
    name: '',
    phone: '',
    organization: '',
    title: '',
    tag: '',
    seat: '',
    companionNote: '',
  }
}

/**
 * 提交同行人员登记并刷新工作台数据。
 *
 * 入参：无；函数读取弹窗目标嘉宾与表单值。
 * 返回值：Promise<void>：登记成功后关闭弹窗并刷新列表。
 * 异常：缺少必填项或后端业务失败时展示对应提示，不向外抛出。
 */
async function submitCompanion(): Promise<void> {
  const target = companionTarget.value
  if (!target) {
    return
  }
  const submittedName = companionForm.value.name.trim()
  const submittedPhone = companionForm.value.phone.trim()
  if (!submittedName || !submittedPhone) {
    ElMessage.warning('请填写同行人员姓名和手机号。')
    return
  }
  if (!isOnline.value) {
    ElMessage.warning('网络连接已断开，请恢复网络后重试。')
    return
  }

  companionSubmitting.value = true
  try {
    await createStaffCompanion(String(route.params.id), {
      ...companionForm.value,
      name: submittedName,
      phone: submittedPhone,
    })
    companionDialogVisible.value = false
    ElMessage.success(`已登记 ${submittedName}，陪同 ${target.name}，并已标记签到。`)
    await loadDetail()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '同行登记失败。'))
  } finally {
    companionSubmitting.value = false
  }
}

/**
 * 将签到时间格式化为当天时分文本。
 *
 * 入参：value 为后端返回的 ISO 时间字符串，必填；空值返回空字符串。
 * 返回值：string：形如 14:05 的时分文本。
 * 异常：非法日期由浏览器按默认结果处理，当前函数不主动抛出异常。
 */
function formatCheckInTime(value: string): string {
  if (!value) {
    return ''
  }
  const date = new Date(value)
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

/**
 * 对核对后的当前嘉宾执行人工签到。
 *
 * 入参：无；函数读取 selectedManualGuest 当前值。
 * 返回值：Promise<void>：签到成功后刷新数据、提示结果并返回搜索列表。
 * 异常：没有选中嘉宾时直接结束；业务异常由 handleManualCheckIn 转换为签到结果。
 */
async function confirmManualCheckIn(): Promise<void> {
  if (!selectedManualGuest.value) {
    return
  }
  await handleManualCheckIn(selectedManualGuest.value.id)
  if (scanFeedback.value?.status === 'success') {
    ElMessage.success('人工签到成功。')
    selectedManualGuest.value = undefined
  } else if (scanFeedback.value?.message) {
    ElMessage.warning(scanFeedback.value.message)
  }
}

/**
 * 退出工作人员会话并返回当前会议专属登录入口。
 *
 * 入参：无；函数读取当前路由会议 ID 和工作人员会话。
 * 返回值：Promise<void>：无论服务端撤销是否成功，均清理本地会话并完成路由跳转。
 * 异常：服务端撤销失败时显示警告但不向外抛出。
 */
async function handleLogout(): Promise<void> {
  const meetingId = String(route.params.id)
  try {
    await logoutClientSession('staff')
  } catch {
    ElMessage.warning('服务端会话可能已失效，本地登录状态已清除。')
  } finally {
    await stopCameraScan()
    session.clearStaff()
    await router.replace(`/meetings/${meetingId}/staff/login`)
  }
}

/**
 * 延迟触发服务端嘉宾搜索，避免连续输入产生过多请求。
 *
 * 入参：无；函数读取当前搜索关键词。
 * 返回值：void：重置 300 毫秒搜索计时器。
 * 异常：搜索接口异常由 loadGuests 转换为页面消息。
 */
function scheduleGuestSearch(): void {
  if (guestSearchTimer !== undefined) {
    window.clearTimeout(guestSearchTimer)
  }
  guestSearchTimer = window.setTimeout(() => { void loadGuests(guestQuery.value) }, 300)
}

/**
 * 同步浏览器当前网络连接状态。
 *
 * 入参：
 *   无；函数读取浏览器 Navigator（导航器）对象的在线状态。
 *
 * 返回值：
 *   void：更新页面网络状态提示和签到按钮可用状态。
 *
 * 异常：
 *   当前函数不主动抛出异常；浏览器不支持网络状态检测时按其默认在线状态处理。
 */
function updateNetworkStatus(): void {
  isOnline.value = navigator.onLine
}

/**
 * 启动工作人员签到页的网络状态监听。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：注册网络连接和断开事件监听，并立即同步一次状态。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function startNetworkMonitoring(): void {
  updateNetworkStatus()
  window.addEventListener('online', updateNetworkStatus)
  window.addEventListener('offline', updateNetworkStatus)
}

/**
 * 停止工作人员签到页的网络状态监听，避免离开页面后残留事件处理器。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：移除网络连接和断开事件监听。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function stopNetworkMonitoring(): void {
  window.removeEventListener('online', updateNetworkStatus)
  window.removeEventListener('offline', updateNetworkStatus)
}

/**
 * 设置工作人员端签到反馈，并按扫码缓冲时间自动清空提示。
 *
 * 入参：result 为需要展示的签到结果，必填；包含状态、提示文案和可选嘉宾信息。
 * 返回值：void：立即更新页面提示；成功或重复签到时同步刷新扫描区下方保留的嘉宾信息。
 * 异常：当前函数不主动抛出异常。
 */
function setScanFeedback(result: ScanResult): void {
  if (scanFeedbackTimer !== undefined) {
    window.clearTimeout(scanFeedbackTimer)
  }
  scanFeedback.value = result
  if (result.status === 'success' && result.guest) {
    latestScannedGuestResult.value = result
  }
  if (result.status === 'already_checked_in' && result.duplicate) {
    latestScannedGuestResult.value = result
  }
  scanFeedbackTimer = window.setTimeout(() => {
    scanFeedback.value = undefined
    scanFeedbackTimer = undefined
  }, cameraScanCooldownMs)
}

/**
 * 清理工作人员端签到反馈自动关闭计时器。
 *
 * 入参：无。
 * 返回值：void：计时器存在时清除，避免离开页面后继续更新状态。
 * 异常：当前函数不主动抛出异常。
 */
function clearScanFeedbackTimer(): void {
  if (scanFeedbackTimer !== undefined) {
    window.clearTimeout(scanFeedbackTimer)
    scanFeedbackTimer = undefined
  }
}

/**
 * 启动手机后置摄像头并识别嘉宾二维码。
 *
 * 入参：无。
 * 返回值：Promise<void>：成功识别后自动填充 token 并执行签到。
 * 异常：摄像头权限被拒绝或浏览器不支持扫码能力时展示提示。
 */
async function startCameraScan(): Promise<void> {
  if (cameraScanning.value) {
    return
  }
  if (!isOnline.value) {
    setScanFeedback({ status: 'invalid', message: '网络连接已断开，请恢复网络后重新签到。' })
    return
  }

  const scanGeneration = ++cameraScanGeneration
  try {
    cameraStarting.value = true
    cameraScanning.value = true
    await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
    if (scanGeneration !== cameraScanGeneration) {
      return
    }

    const video = document.getElementById('staff-qr-reader') as HTMLVideoElement | null
    if (!video) {
      throw new Error('无法找到视频容器。')
    }

    scanStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' },
    })
    video.srcObject = scanStream
    video.setAttribute('playsinline', '')
    await video.play()

    if (scanGeneration !== cameraScanGeneration) {
      scanStream.getTracks().forEach((t) => t.stop())
      scanStream = null
      return
    }
    cameraStarting.value = false

    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d', { willReadFrequently: true })

    const scanLoop = (): void => {
      if (scanGeneration !== cameraScanGeneration) return
      if (!ctx) return
      if (video.readyState !== video.HAVE_ENOUGH_DATA) {
        scanAnimationId = requestAnimationFrame(scanLoop)
        return
      }
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      ctx.drawImage(video, 0, 0)
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
      const code = jsQR(imageData.data, imageData.width, imageData.height, {
        inversionAttempts: 'dontInvert',
      })
      if (code && code.data && shouldAcceptCameraToken(code.data)) {
        qrToken.value = code.data
        void handleScan()
      }
      scanAnimationId = requestAnimationFrame(scanLoop)
    }
    scanAnimationId = requestAnimationFrame(scanLoop)
  } catch {
    if (scanGeneration === cameraScanGeneration) {
      await stopCameraScan()
      ElMessage.error('无法打开摄像头，请检查权限后重试。')
    }
  }
}

/**
 * 判断摄像头识别到的二维码是否允许提交签到。
 *
 * 入参：decodedText 为当前帧识别到的二维码文本，必填。
 * 返回值：boolean：网络可用、当前未提交中，且未命中短时间重复 token 时返回 true。
 * 异常：当前函数不主动抛出异常。
 */
function shouldAcceptCameraToken(decodedText: string): boolean {
  const normalizedToken = decodedText.trim()
  if (!normalizedToken || loading.value || !isOnline.value) {
    return false
  }
  const now = Date.now()
  if (now - lastCameraTokenAt < cameraScanCooldownMs) {
    return false
  }
  if (normalizedToken === lastCameraToken && now - lastCameraTokenAt < sameCameraTokenCooldownMs) {
    return false
  }
  // 记录最近识别 token，避免同一个二维码停留在画面中连续触发提交。
  lastCameraToken = normalizedToken
  lastCameraTokenAt = now
  return true
}

/**
 * 停止摄像头扫码并释放媒体设备资源。
 *
 * 入参：无。
 * 返回值：Promise<void>：立即退出扫码界面，并停止视频轨道和扫描循环。
 */
async function stopCameraScan(): Promise<void> {
  cameraScanGeneration += 1
  if (scanAnimationId !== null) {
    cancelAnimationFrame(scanAnimationId)
    scanAnimationId = null
  }
  if (scanStream) {
    scanStream.getTracks().forEach((t) => t.stop())
    scanStream = null
  }
  lastCameraToken = ''
  lastCameraTokenAt = 0
  cameraStarting.value = false
  cameraScanning.value = false
}

/**
 * 加载工作人员签到工作台所需数据。
 *
 * 入参：
 *   无；函数从当前路由参数读取会议 ID。
 *
 * 返回值：
 *   Promise<void>：加载完成后更新会议、参会人员和签到列表。
 *
 * 异常：登录过期、会议未授权或网络异常时展示页面错误。
 */
async function loadDetail(): Promise<void> {
  const meetingId = String(route.params.id)
  pageLoading.value = true
  pageError.value = ''
  try {
    const [meetingData, guestData, checkInData, checkInSessionData] = await Promise.all([
      listStaffMeetings(),
      searchStaffGuests(meetingId, ''),
      listStaffCheckIns(meetingId),
      getStaffCheckInSession(meetingId),
    ])
    meeting.value = meetingData.find((item) => item.id === meetingId)
    if (!meeting.value) {
      throw new Error('会议不存在或无签到权限。')
    }
    guests.value = guestData
    displayedGuests.value = guestData
    checkIns.value = checkInData
    currentCheckInSession.value = checkInSessionData
  } catch (error) {
    meeting.value = undefined
    currentCheckInSession.value = undefined
    pageError.value = getApiErrorMessage(error, '签到工作台加载失败。')
  } finally {
    pageLoading.value = false
  }
}

/**
 * 调用服务端按关键词查询嘉宾。
 *
 * 入参：query 为姓名、手机号、单位或座位关键词，可为空。
 * 返回值：Promise<void>：成功后更新当前展示结果。
 * 异常：接口异常时保留原列表并展示消息提示。
 */
async function loadGuests(query: string): Promise<void> {
  try {
    displayedGuests.value = await searchStaffGuests(String(route.params.id), query.trim())
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '嘉宾搜索失败。'))
  }
}

/**
 * 重新加载签到记录。
 *
 * 入参：
 *   无；函数从当前路由参数读取会议 ID。
 *
 * 返回值：
 *   Promise<void>：加载完成后更新签到列表和参会人员状态。
 *
 * 异常：
 *   任一刷新接口失败时向调用方抛出异常，由签到操作流程展示错误提示。
 */
async function refreshCheckIns(): Promise<void> {
  const meetingId = String(route.params.id)
  const [guestData, displayedGuestData, checkInData, checkInSessionData] = await Promise.all([
    searchStaffGuests(meetingId, ''),
    searchStaffGuests(meetingId, guestQuery.value.trim()),
    listStaffCheckIns(meetingId),
    getStaffCheckInSession(meetingId),
  ])
  guests.value = guestData
  displayedGuests.value = displayedGuestData
  checkIns.value = checkInData
  currentCheckInSession.value = checkInSessionData
}

/**
 * 重复签到后尽量刷新本地签到状态。
 *
 * 入参：无；函数读取当前路由会议 ID 和搜索关键词。
 * 返回值：Promise<void>：刷新成功或失败都会结束，不影响重复签到提示展示。
 * 异常：刷新异常会被当前函数吸收，并通过轻量提示告知工作人员。
 */
async function refreshAfterDuplicateCheckIn(): Promise<void> {
  try {
    await refreshCheckIns()
  } catch {
    ElMessage.warning('重复签到信息已返回，但本地列表刷新失败，请稍后手动刷新页面。')
  }
}

/**
 * 根据签到状态计算 Element Plus 提示类型。
 *
 * 入参：
 *   无；函数读取当前签到结果状态。
 *
 * 返回值：
 *   'success' | 'warning' | 'error' | 'info'：适用于 el-alert 的类型。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function alertType(): 'success' | 'warning' | 'error' | 'info' {
  if (!scanFeedback.value) {
    return 'info'
  }

  if (scanFeedback.value.status === 'success') {
    return 'success'
  }

  if (scanFeedback.value.status === 'already_checked_in') {
    return 'warning'
  }

  return 'error'
}

/**
 * 执行扫码签到。
 *
 * 入参：
 *   无；函数从路由读取会议 ID，从会话读取工作人员 ID，从表单读取二维码 token。
 *
 * 返回值：
 *   Promise<void>：签到完成后更新结果和签到列表。
 *
 * 异常：缺少会话或 token 时展示错误；后端业务和网络异常转换为签到结果。
 */
async function handleScan(): Promise<void> {
  if (!session.staff) {
    setScanFeedback({ status: 'invalid', message: '请先完成工作人员登录。' })
    return
  }

  // 网络断开时不提交新的签到请求，避免工作人员误以为操作已成功。
  if (!isOnline.value) {
    setScanFeedback({ status: 'invalid', message: '网络连接已断开，请恢复网络后重新签到。' })
    return
  }

  if (!qrToken.value.trim()) {
    setScanFeedback({ status: 'invalid', message: '请填写嘉宾二维码 token。' })
    return
  }

  loading.value = true
  try {
    const record = await scanStaffCheckIn(String(route.params.id), qrToken.value.trim())
    await refreshCheckIns()
    const guest = guests.value.find((item) => item.id === record.guestId)
    setScanFeedback({
      status: 'success',
      message: '签到成功。',
      guest: guest ? { ...guest, meetingId: record.meetingId, qrToken: '' } : undefined,
      checkIn: record,
    })
  } catch (error) {
    const duplicate = getAlreadyCheckedInDetail(error)
    if (duplicate) {
      await refreshAfterDuplicateCheckIn()
      setScanFeedback({ status: 'already_checked_in', message: duplicate.message, duplicate })
      return
    }
    const message = getApiErrorMessage(error, '扫码签到失败。')
    setScanFeedback({ status: message.includes('已签到') ? 'already_checked_in' : 'invalid', message })
  } finally {
    loading.value = false
  }
}

/**
 * 手动标记嘉宾签到。
 *
 * 入参：
 *   guestId：嘉宾 ID，必填。
 *
 * 返回值：
 *   Promise<void>：手动签到完成后更新结果和签到列表。
 *
 * 异常：缺少工作人员会话时展示错误；后端业务和网络异常转换为签到结果。
 */
async function handleManualCheckIn(guestId: string): Promise<void> {
  if (!session.staff) {
    setScanFeedback({ status: 'invalid', message: '请先完成工作人员登录。' })
    return
  }

  // 网络断开时不提交新的签到请求，避免产生无法确认的现场状态。
  if (!isOnline.value) {
    setScanFeedback({ status: 'invalid', message: '网络连接已断开，请恢复网络后重新签到。' })
    return
  }

  manualLoadingId.value = guestId
  try {
    const record = await manualStaffCheckIn(String(route.params.id), guestId)
    await refreshCheckIns()
    const guest = guests.value.find((item) => item.id === record.guestId)
    setScanFeedback({
      status: 'success',
      message: '人工签到成功。',
      guest: guest ? { ...guest, meetingId: record.meetingId, qrToken: '' } : undefined,
      checkIn: record,
    })
  } catch (error) {
    const duplicate = getAlreadyCheckedInDetail(error)
    if (duplicate) {
      await refreshAfterDuplicateCheckIn()
      setScanFeedback({ status: 'already_checked_in', message: duplicate.message, duplicate })
      return
    }
    const message = getApiErrorMessage(error, '人工签到失败。')
    setScanFeedback({ status: message.includes('已签到') ? 'already_checked_in' : 'invalid', message })
  } finally {
    manualLoadingId.value = ''
  }
}

/**
 * 跳转到当前会议专属工作人员登录页。
 *
 * 入参：
 *   无。
 *
 * 返回值：Promise<void>：完成当前会议工作人员登录页跳转。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
async function goLogin(): Promise<void> {
  await router.push(`/meetings/${String(route.params.id)}/staff/login`)
}

/**
 * 格式化日期时间展示。
 *
 * 入参：
 *   value：ISO 日期字符串，必填。
 *
 * 返回值：
 *   string：中文本地化日期时间文本。
 *
 * 异常：
 *   当前函数不主动抛出异常；非法日期会按浏览器默认结果展示。
 */
function formatDate(value: string): string {
  return new Date(value).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}

/**
 * 将签到方式转换为中文文本。
 *
 * 入参：
 *   method：签到方式，必填，可取 scan 或 manual。
 *
 * 返回值：
 *   string：中文签到方式文本。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function methodText(method: CheckInRecord['method']): string {
  const map: Record<CheckInRecord['method'], string> = {
    scan: '扫码',
    manual: '手动',
  }
  return map[method]
}

onMounted(loadDetail)
onMounted(startNetworkMonitoring)
watch(guestQuery, scheduleGuestSearch)
onUnmounted(stopNetworkMonitoring)
onUnmounted(() => {
  if (guestSearchTimer !== undefined) window.clearTimeout(guestSearchTimer)
  clearScanFeedbackTimer()
  void stopCameraScan()
})
</script>
