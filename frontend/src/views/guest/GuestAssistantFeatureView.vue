<template>
  <section class="assistant-page">
    <header class="assistant-page__header is-service">
      <button type="button" class="assistant-page__back" aria-label="返回" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </button>
      <h1 class="assistant-page__header-title">{{ feature?.title ?? '会议服务' }}</h1>
    </header>

    <main class="assistant-page__body" :class="{ 'is-agenda': isAgendaFeature }">
      <el-skeleton v-if="loading" :rows="6" animated />
      <el-alert v-else-if="errorMessage" type="error" :closable="false" :title="errorMessage" />
      <el-alert v-else-if="feature && !feature.isPublished" type="info" :closable="false" :title="feature.unpublishedMessage" />

      <template v-else-if="feature?.key === 'agenda'">
        <section class="assistant-agenda">
          <nav
            v-if="agendaGroups.length > 1"
            class="assistant-agenda-days"
            role="tablist"
            aria-label="选择会议日期"
          >
            <button
              v-for="group in agendaGroups"
              :id="`agenda-tab-${group.id}`"
              :key="group.id"
              type="button"
              role="tab"
              :aria-controls="`agenda-panel-${group.id}`"
              :aria-selected="activeAgendaGroup?.id === group.id"
              :class="{ 'is-active': activeAgendaGroup?.id === group.id }"
              @click="activeAgendaDateId = group.id"
            >
              <strong>{{ group.day || group.title }}</strong>
              <span v-if="group.day">{{ group.monthLabel }} {{ group.weekday }}</span>
            </button>
          </nav>

          <p v-if="activeAgendaGroup" class="assistant-agenda-summary">
            <el-icon><Calendar /></el-icon>
            {{ agendaSummary }}
          </p>

          <div
            v-if="activeAgendaGroup"
            :id="`agenda-panel-${activeAgendaGroup.id}`"
            class="assistant-agenda-timeline"
            role="tabpanel"
            :aria-labelledby="agendaGroups.length > 1 ? `agenda-tab-${activeAgendaGroup.id}` : undefined"
          >
            <template v-for="item in activeAgendaGroup.items" :key="item.id">
              <header v-if="item.kind === 'section'" class="assistant-agenda-section">
                <strong>{{ item.period }}</strong>
                <span v-if="item.title">{{ item.title }}</span>
              </header>

              <article v-else class="assistant-agenda-entry">
                <time class="assistant-agenda-entry__time">
                  <strong>{{ item.startTime || '待定' }}</strong>
                  <span v-if="item.endTime">{{ item.endTime }}</span>
                </time>
                <span class="assistant-agenda-entry__rail" aria-hidden="true"></span>
                <div class="assistant-agenda-entry__content">
                  <span class="assistant-agenda-entry__kind">{{ item.title }}</span>
                  <!-- 内容在解析阶段经过标签白名单清洗，只允许加粗、换行、段落和缩进结构。 -->
                  <div
                    v-if="item.contentHtml"
                    class="assistant-agenda-entry__rich-content"
                    v-html="item.contentHtml"
                  ></div>
                  <p v-if="item.location" class="assistant-agenda-entry__location">
                    <el-icon><LocationIcon /></el-icon>
                    {{ item.location }}
                  </p>
                </div>
              </article>
            </template>
          </div>
        </section>
      </template>

      <template v-else-if="feature?.key === 'manual'">
        <section v-if="materials.length" class="meeting-material-list" aria-label="会议资料列表">
          <article
            v-for="material in materials"
            :key="material.id"
            class="meeting-material-card"
            :class="{ 'is-expanded': isMaterialExpanded(material.id) }"
          >
            <button
              type="button"
              class="meeting-material-card__heading"
              :aria-expanded="isMaterialExpanded(material.id)"
              :aria-controls="`material-content-${material.id}`"
              @click="toggleMaterial(material.id)"
            >
              <span class="meeting-material-card__icon"><el-icon><Document /></el-icon></span>
              <span class="meeting-material-card__title">
                <strong>{{ material.title }}</strong>
                <small v-if="material.originalFilename">含可下载附件</small>
              </span>
              <span class="meeting-material-card__toggle" aria-hidden="true">
                <el-icon><ArrowUp v-if="isMaterialExpanded(material.id)" /><ArrowDown v-else /></el-icon>
              </span>
            </button>
            <el-collapse-transition>
              <div
                v-show="isMaterialExpanded(material.id)"
                :id="`material-content-${material.id}`"
                class="meeting-material-card__details"
              >
                <!-- 资料正文已在解码阶段经过标签白名单清洗，只展示受限文档格式。 -->
                <div
                  v-if="material.content"
                  class="meeting-material-card__content"
                  v-html="materialContentHtml(material)"
                ></div>
                <button
                  v-if="material.originalFilename"
                  type="button"
                  class="meeting-material-card__download"
                  :disabled="downloadingMaterialId === material.id"
                  @click="downloadMaterial(material)"
                >
                  <span class="meeting-material-card__file">
                    <el-icon><Paperclip /></el-icon>
                    <span>
                      <strong>{{ material.originalFilename }}</strong>
                      <small>{{ formatMaterialFileSize(material.sizeBytes) }}</small>
                    </span>
                  </span>
                  <span class="meeting-material-card__download-action">
                    <el-icon><Download /></el-icon>
                    {{ downloadingMaterialId === material.id ? '下载中' : '下载' }}
                  </span>
                </button>
              </div>
            </el-collapse-transition>
          </article>
        </section>
        <div v-else class="assistant-content-cards">
          <article class="assistant-content-card">{{ feature.content || '会议资料待补充。' }}</article>
        </div>
      </template>

      <template v-else-if="feature?.key === 'weather'">
        <template v-if="!weather?.available || !weather.current">
          <section class="weather-empty" aria-live="polite">
            <el-icon class="weather-empty__icon"><Sunny /></el-icon>
            <p class="weather-empty__title">天气数据暂时不可用</p>
            <p class="weather-empty__desc">{{ weather?.message || '请稍后再试。' }}</p>
            <el-button class="weather-empty__action" type="primary" plain @click="loadFeature">重新加载</el-button>
          </section>
        </template>

        <template v-else>
          <section class="weather-card">
            <header class="weather-card__head">
              <p class="weather-card__location">
                <el-icon><LocationIcon /></el-icon>
                <span>{{ weather.locationName }}</span>
              </p>
            </header>

            <button
              type="button"
              class="weather-card__now"
              :class="{ 'is-expanded': hourlyExpanded }"
              :aria-expanded="hourlyExpanded"
              aria-controls="weather-hourly-section"
              @click="hourlyExpanded = !hourlyExpanded"
            >
              <span class="weather-card__now-icon" aria-hidden="true">{{ weatherIcon(weather.current.iconCode) }}</span>
              <div class="weather-card__now-temp">
                <strong>{{ weather.current.temperature }}<small>°</small></strong>
                <span>{{ weather.current.condition }}</span>
              </div>
              <dl class="weather-card__now-meta">
                <div>
                  <dt>湿度</dt>
                  <dd>{{ weather.current.humidity }}%</dd>
                </div>
                <div>
                  <dt>风速</dt>
                  <dd>{{ weather.current.windSpeed }} km/h</dd>
                </div>
              </dl>
              <span class="weather-card__now-toggle" aria-hidden="true">
                <el-icon><ArrowDown v-if="!hourlyExpanded" /><ArrowUp v-else /></el-icon>
              </span>
            </button>

            <section
              v-if="hourlyExpanded && weather.hourly.length"
              id="weather-hourly-section"
              class="weather-card__hourly"
              aria-label="未来几小时预报"
            >
              <ul>
                <li v-for="item in weather.hourly" :key="item.forecastAt">
                  <span class="weather-hourly-item__time">{{ formatHourlyTime(item.forecastAt) }}</span>
                  <span class="weather-hourly-item__icon" aria-hidden="true">{{ weatherIcon(item.iconCode) }}</span>
                  <span class="weather-hourly-item__condition">{{ item.condition }}</span>
                  <span class="weather-hourly-item__temp"><strong>{{ item.temperature }}°</strong></span>
                  <span v-if="item.precipitationProbability > 0" class="weather-hourly-item__pop">
                    <el-icon><Umbrella /></el-icon>{{ item.precipitationProbability }}%
                  </span>
                </li>
              </ul>
            </section>

            <section v-if="weather.tips.length" class="weather-tips" aria-label="温馨提示">
              <h3>温馨提示</h3>
              <ul>
                <li v-for="(tip, index) in weather.tips" :key="index">{{ tip }}</li>
              </ul>
            </section>

            <section class="weather-card__forecast" aria-label="近期预报">
              <h2>近期预报</h2>
              <ul>
                <li
                  v-for="item in upcomingForecast"
                  :key="item.date"
                  :class="{ 'is-today': item.date === todayKey }"
                >
                  <span class="weather-forecast-item__date">
                    <strong>{{ formatForecastShort(item.date) }}</strong>
                    <small>{{ isToday(item.date) ? '今天' : formatWeekday(item.date) }}</small>
                  </span>
                  <span class="weather-forecast-item__icon" aria-hidden="true">{{ weatherIcon(item.iconCode) }}</span>
                  <span class="weather-forecast-item__condition">{{ item.condition }}</span>
                  <span v-if="item.precipitation > 0" class="weather-forecast-item__rain">
                    <el-icon><Umbrella /></el-icon>{{ item.precipitation }}mm
                  </span>
                  <span class="weather-forecast-item__temperature">
                    <strong>{{ item.high }}°</strong>
                    <em>{{ item.low }}°</em>
                  </span>
                </li>
              </ul>
            </section>
          </section>

          <a class="weather-source" :href="weather.sourceUrl" target="_blank" rel="noopener noreferrer">
            数据由 {{ weather.sourceName }} 提供
          </a>
        </template>
      </template>

      <template v-else-if="feature?.key === 'route'">
        <section class="route-navigation-card">
          <div class="route-navigation-card__icon"><el-icon><LocationIcon /></el-icon></div>
          <div>
            <h2>{{ meeting?.navigationName || meeting?.location || '会议地点' }}</h2>
            <p>{{ meeting?.navigationAddress || meeting?.location || '管理员尚未补充会议地址。' }}</p>
          </div>
          <a
            v-if="navigationUrl"
            class="route-navigation-button"
            :href="navigationUrl"
            target="_blank"
            rel="noopener noreferrer"
          >
            打开地图导航
          </a>
          <el-alert v-else type="warning" :closable="false" title="管理员尚未选择准确的导航位置。" />
        </section>

        <section class="route-arrival-guide">
          <h2>到场说明</h2>
          <article v-for="(block, index) in contentBlocks" :key="`route-${index}`" class="assistant-content-card">{{ block }}</article>
        </section>
      </template>

      <template v-else-if="feature?.key === 'contact'">
        <div v-if="!contactPersons.length" class="assistant-content-cards">
          <article class="assistant-content-card">联系人信息待补充</article>
        </div>
        <ul v-else class="contact-person-list">
          <li v-for="(person, index) in contactPersons" :key="`${person.name}-${index}`" class="contact-person-card">
            <span class="contact-person-card__avatar" aria-hidden="true">{{ person.name.slice(0, 1) }}</span>
            <div class="contact-person-card__info">
              <strong>{{ person.name }}</strong>
              <small v-if="person.role">{{ person.role }}</small>
            </div>
            <a
              v-if="person.phone"
              class="contact-person-card__call"
              :href="`tel:${person.phone}`"
              :aria-label="`拨打 ${person.name}`"
            >
              <el-icon><Phone /></el-icon>
            </a>
            <span v-else class="contact-person-card__call is-disabled" aria-hidden="true">
              <el-icon><Phone /></el-icon>
            </span>
          </li>
        </ul>
      </template>

      <div v-else-if="feature" class="assistant-content-cards">
        <article v-for="(block, index) in contentBlocks" :key="`${feature.key}-${index}`" class="assistant-content-card">{{ block }}</article>
      </div>
    </main>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ArrowDown, ArrowLeft, ArrowUp, Calendar, Document, Download, Location as LocationIcon, Paperclip, Phone, Sunny, Umbrella } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import { getApiErrorMessage } from '../../api/client'
import { getPublicMeeting } from '../../api/sessions'
import {
  getGuestMeetingAssistantFeature,
  getPublicMeetingAssistantFeature,
  isMeetingAssistantFeatureKey,
} from '../../api/meetingAssistant'
import {
  downloadMeetingMaterialAttachment,
  listGuestMeetingMaterials,
  listPublicMeetingMaterials,
  saveMeetingMaterialBlob,
} from '../../api/meetingMaterials'
import { getGuestMeetingWeather, getPublicMeetingWeather, type MeetingWeather } from '../../api/meetingWeather'
import type { Meeting, MeetingAssistantFeature, MeetingMaterial } from '../../types'
import { decodeMaterialRichContent } from '../../utils/materialRichText'
import {
  agendaPlainTextToHtml,
  decodeAgendaRichContent,
  isEncodedAgendaRichContent,
} from '../../utils/agendaRichText'

interface AgendaEntryItem {
  id: string
  kind: 'entry'
  startTime: string
  endTime: string
  title: string
  contentHtml: string
  location: string
}

interface AgendaSectionItem {
  id: string
  kind: 'section'
  period: string
  title: string
}

type AgendaGroupItem = AgendaEntryItem | AgendaSectionItem

interface AgendaDateGroup {
  id: string
  title: string
  day: string
  monthLabel: string
  weekday: string
  dateKey: string
  items: AgendaGroupItem[]
}

interface AgendaDateMeta {
  title: string
  day: string
  monthLabel: string
  weekday: string
  dateKey: string
  period: string
}

const route = useRoute()
const router = useRouter()
const meeting = ref<Meeting>()
const feature = ref<MeetingAssistantFeature>()
const weather = ref<MeetingWeather>()
const materials = ref<MeetingMaterial[]>([])
const loading = ref(true)
const downloadingMaterialId = ref('')
const expandedMaterialIds = ref<string[]>([])
const hourlyExpanded = ref(false)
const activeAgendaDateId = ref('')
const errorMessage = ref('')
const agendaGroups = computed(buildAgendaGroups)
const activeAgendaGroup = computed(buildActiveAgendaGroup)
const agendaSummary = computed(buildAgendaSummary)
const contentBlocks = computed(buildContentBlocks)
const navigationUrl = computed(buildNavigationUrl)
const upcomingForecast = computed(buildUpcomingForecast)
const contactPersons = computed(buildContactPersons)
const isPublicAccess = computed(() => route.query.access === 'public')
const isAgendaFeature = computed(() => String(route.params.featureKey) === 'agenda')

/**
 * 返回 7 日预报中从明天开始的列表，跳过与实时卡片重复的"今天"项。
 *
 * 入参：无；函数读取 weather.daily。
 * 返回值：MeetingDailyWeather[]：去掉了今天条目的预报列表；若 daily 为空则返回空数组。
 * 异常：当前函数不主动抛出异常。
 */
function buildUpcomingForecast(): NonNullable<typeof weather.value>['daily'] {
  return weather.value?.daily.slice(1) ?? []
}

/**
 * 将联系会务配置转换为嘉宾端可拨号的联系人列表。
 *
 * 入参：无；函数读取当前 feature 的 contacts 字段。
 * 返回值：Array<{name, role, phone}>：已清理空白后的联系人列表；缺失时返回空数组。
 * 异常：当前函数不主动抛出异常。
 */
function buildContactPersons(): Array<{ name: string; role: string; phone: string }> {
  return feature.value?.contacts ?? []
}

/**
 * 加载会议基础信息和当前会议助手功能配置。
 *
 * 入参：无；函数读取路由中的会议 ID 和功能标识。
 * 返回值：Promise<void>：完成后更新会议、功能配置和页面状态。
 * 异常：会议或功能不存在、网络失败时转换为页面错误提示。
 */
async function loadFeature(): Promise<void> {
  const meetingId = String(route.params.id)
  const featureKey = String(route.params.featureKey)
  loading.value = true
  errorMessage.value = ''
  try {
    if (!isMeetingAssistantFeatureKey(featureKey)) {
      errorMessage.value = '未找到对应的会议服务。'
      return
    }
    const featureRequest = isPublicAccess.value
      ? getPublicMeetingAssistantFeature(meetingId, featureKey)
      : getGuestMeetingAssistantFeature(meetingId, featureKey)
    const [meetingData, featureData] = await Promise.all([
      getPublicMeeting(meetingId),
      featureRequest,
    ])
    meeting.value = meetingData
    feature.value = featureData
    if (featureKey === 'agenda' && featureData.isPublished) {
      selectDefaultAgendaDate()
    }
    if (featureKey === 'manual' && featureData.isPublished) {
      materials.value = isPublicAccess.value
        ? await listPublicMeetingMaterials(meetingId)
        : await listGuestMeetingMaterials(meetingId)
      // 嘉宾首次进入只浏览标题，避免长资料占据整个首屏。
      expandedMaterialIds.value = []
    }
    if (featureKey === 'weather' && featureData.isPublished) {
      weather.value = isPublicAccess.value
        ? await getPublicMeetingWeather(meetingId)
        : await getGuestMeetingWeather(meetingId)
    }
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '会议服务加载失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

/**
 * 判断指定会议资料是否处于展开状态。
 *
 * 入参：materialId 为必填资料 ID。
 * 返回值：boolean：当前资料已展开时返回 true，否则返回 false。
 * 异常：当前函数不主动抛出异常。
 */
function isMaterialExpanded(materialId: string): boolean {
  return expandedMaterialIds.value.includes(materialId)
}

/**
 * 独立切换指定资料的展开状态。
 *
 * 入参：materialId 为必填资料 ID。
 * 返回值：void：已展开时收起，已收起时追加到展开列表；其他资料状态保持不变。
 * 异常：当前函数不主动抛出异常。
 */
function toggleMaterial(materialId: string): void {
  if (isMaterialExpanded(materialId)) {
    expandedMaterialIds.value = expandedMaterialIds.value.filter((id) => id !== materialId)
    return
  }
  expandedMaterialIds.value = [...expandedMaterialIds.value, materialId]
}

/**
 * 将会议资料正文转换为嘉宾端可安全展示的文档 HTML。
 *
 * 入参：material 为必填会议资料，可以包含历史普通文本或新版编码内容。
 * 返回值：string：经过白名单清洗的段落、加粗、列表和缩进结构。
 * 异常：编码损坏时安全回退为普通文本，不向页面抛出异常。
 */
function materialContentHtml(material: MeetingMaterial): string {
  return decodeMaterialRichContent(material.content)
}

/**
 * 下载嘉宾当前选择的会议资料附件。
 *
 * 入参：material 为包含附件的会议资料，必填。
 * 返回值：Promise<void>：下载成功后使用原始文件名触发浏览器保存。
 * 异常：权限、附件或网络异常时转换为页面消息提示。
 */
async function downloadMaterial(material: MeetingMaterial): Promise<void> {
  if (!material.originalFilename) {
    return
  }
  downloadingMaterialId.value = material.id
  try {
    const access = isPublicAccess.value ? 'public' : 'guest'
    const blob = await downloadMeetingMaterialAttachment(
      String(route.params.id),
      material.id,
      access,
    )
    saveMeetingMaterialBlob(blob, material.originalFilename)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '附件下载失败，请稍后重试。'))
  } finally {
    downloadingMaterialId.value = ''
  }
}

/**
 * 将附件字节数转换为嘉宾易读的文件大小。
 *
 * 入参：sizeBytes 为可空附件字节数。
 * 返回值：string：无大小时返回“可下载附件”，否则返回 KB 或 MB 文本。
 * 异常：当前函数不主动抛出异常。
 */
function formatMaterialFileSize(sizeBytes?: number): string {
  if (!sizeBytes) {
    return '可下载附件'
  }
  if (sizeBytes >= 1024 * 1024) {
    return `${(sizeBytes / 1024 / 1024).toFixed(1)} MB`
  }
  return `${Math.max(sizeBytes / 1024, 0.1).toFixed(1)} KB`
}

/**
 * 返回当前会议的嘉宾首页，并自动展开会议服务列表。
 *
 * 入参：无；函数读取当前路由中的会议 ID。
 * 返回值：Promise<void>：公开模式返回会议入口；登录模式返回嘉宾首页并展开服务抽屉。
 * 异常：路由跳转失败时由 Vue Router 抛出异常。
 */
async function goBack(): Promise<void> {
  if (isPublicAccess.value) {
    await router.push(`/meetings/${String(route.params.id)}`)
    return
  }
  await router.push({
    path: `/guest/meetings/${String(route.params.id)}`,
    query: { services: 'open' },
  })
}

/**
 * 将管理员逐行编辑的日程正文转换为按日期组织的展示分组。
 *
 * 入参：无；函数读取当前已发布日程正文，正文可以为空。
 * 返回值：AgendaDateGroup[]：按出现顺序排列的日期分组，每组包含时段标题和日程条目。
 * 异常：当前函数不主动抛出异常；正文为空或没有日期行时使用“全部日程”安全回退。
 * 使用示例：日期行写作 `8月18日（周二）`，时段行写作 `上午｜主旨演讲`，
 * 日程行写作 `09:00-09:30 开幕致辞｜主办方代表｜主会场`。
 */
function buildAgendaGroups(): AgendaDateGroup[] {
  const lines = feature.value?.content.split('\n').map((line) => line.trim()).filter(Boolean) ?? []
  if (!lines.length) {
    return [{
      id: 'agenda-all',
      title: '全部日程',
      day: '',
      monthLabel: '',
      weekday: '',
      dateKey: '',
      items: [parseAgendaEntryLine('日程内容待补充', 0)],
    }]
  }

  const groups: AgendaDateGroup[] = []
  let currentGroup: AgendaDateGroup | undefined

  lines.forEach((line, index) => {
    const dateMeta = parseAgendaDateLine(line)
    if (dateMeta) {
      currentGroup = {
        id: `agenda-date-${dateMeta.dateKey || index}-${index}`,
        title: dateMeta.title,
        day: dateMeta.day,
        monthLabel: dateMeta.monthLabel,
        weekday: dateMeta.weekday,
        dateKey: dateMeta.dateKey,
        items: [],
      }
      groups.push(currentGroup)
      // 日期行末尾带有“上午”等时段时，立即建立对应分段，避免信息丢失。
      if (dateMeta.period) {
        currentGroup.items.push({
          id: `agenda-section-${index}`,
          kind: 'section',
          period: dateMeta.period,
          title: '',
        })
      }
      return
    }

    if (!currentGroup) {
      currentGroup = {
        id: 'agenda-all',
        title: '全部日程',
        day: '',
        monthLabel: '',
        weekday: '',
        dateKey: '',
        items: [],
      }
      groups.push(currentGroup)
    }

    const section = parseAgendaSectionLine(line, index)
    currentGroup.items.push(section ?? parseAgendaEntryLine(line, index))
  })

  return groups
}

/**
 * 解析单个日期标题，并提取日期切换器所需的年月日、星期与可选时段。
 *
 * 入参：
 * - line：必填，非空日程正文行；支持中文日期和使用 `-`、`/`、`.` 分隔的数字日期。
 * 返回值：AgendaDateMeta | null：识别成功返回规范化日期信息，否则返回 null。
 * 异常：当前函数不主动抛出异常；不合法日期只会被视为普通日程正文。
 * 使用示例：`8月18日（周二）上午` 返回 18 日、8 月、周二和上午。
 */
function parseAgendaDateLine(line: string): AgendaDateMeta | null {
  const chineseMatch = line.match(
    /^(?:(\d{4})\s*年\s*)?(\d{1,2})\s*月\s*(\d{1,2})\s*日?\s*(?:[（(]?\s*(周[一二三四五六日天])\s*[）)]?)?\s*(上午|中午|下午|晚上|全天)?$/,
  )
  const numericMatch = line.match(
    /^(?:(\d{4})\s*[-/.]\s*)?(\d{1,2})\s*[-/.]\s*(\d{1,2})\s*(?:[（(]?\s*(周[一二三四五六日天])\s*[）)]?)?\s*(上午|中午|下午|晚上|全天)?$/,
  )
  const match = chineseMatch ?? numericMatch
  if (!match) {
    return null
  }

  const [, year = '', month, day, weekday = '', period = ''] = match
  const numericMonth = Number(month)
  const numericDay = Number(day)
  // 只接受真实月份和日的基础范围，防止普通编号被误判为日期。
  if (numericMonth < 1 || numericMonth > 12 || numericDay < 1 || numericDay > 31) {
    return null
  }

  const normalizedWeekday = weekday === '周天' ? '周日' : weekday
  const paddedMonth = String(numericMonth).padStart(2, '0')
  const paddedDay = String(numericDay).padStart(2, '0')
  return {
    title: `${numericMonth}月${numericDay}日${normalizedWeekday ? ` ${normalizedWeekday}` : ''}`,
    day: String(numericDay),
    monthLabel: `${numericMonth}月`,
    weekday: normalizedWeekday,
    dateKey: year ? `${year}-${paddedMonth}-${paddedDay}` : `${paddedMonth}-${paddedDay}`,
    period,
  }
}

/**
 * 解析上午、下午等时段标题，形成时间轴中的视觉分段。
 *
 * 入参：
 * - line：必填，待识别的非空正文行。
 * - index：必填，大于等于 0 的正文行序号，用于生成稳定展示标识。
 * 返回值：AgendaSectionItem | null：识别成功返回时段与可选主题，否则返回 null。
 * 异常：当前函数不主动抛出异常。
 * 使用示例：`下午｜评价技术创新与成果发布` 返回“下午”分段及对应主题。
 */
function parseAgendaSectionLine(line: string, index: number): AgendaSectionItem | null {
  const match = line.match(/^(上午|中午|下午|晚上|全天)(?:\s*[|｜]\s*(.+))?$/)
  if (!match) {
    return null
  }
  return {
    id: `agenda-section-${index}`,
    kind: 'section',
    period: match[1],
    title: match[2]?.trim() ?? '',
  }
}

/**
 * 解析单个日程行，拆分起止时间、环节名称、受限富文本内容和地点。
 *
 * 入参：
 * - line：必填，待解析的日程正文行；允许没有时间或没有竖线补充字段。
 * - index：必填，大于等于 0 的正文行序号，用于生成稳定展示标识。
 * 返回值：AgendaEntryItem：可直接用于时间轴渲染的日程条目。
 * 异常：当前函数不主动抛出异常；无法识别的内容仍完整保留为环节名称。
 * 使用示例：`09:00-09:30 开幕致辞｜rich:...｜主会场`。
 */
function parseAgendaEntryLine(line: string, index: number): AgendaEntryItem {
  const timeMatch = line.match(
    /^(\d{1,2}:\d{2})(?:\s*[-–—~至]\s*(\d{1,2}:\d{2}))?\s*(.*)$/,
  )
  const content = timeMatch?.[3]?.trim() || line
  // 保留空分段的位置，避免内容为空时把地点错误移动到内容字段。
  const contentParts = content.split(/\s*[|｜]\s*/).map((part) => part.trim())
  const encodedContent = contentParts[1] ?? ''
  if (isEncodedAgendaRichContent(encodedContent)) {
    return {
      id: `agenda-entry-${index}`,
      kind: 'entry',
      startTime: timeMatch?.[1] ?? '',
      endTime: timeMatch?.[2] ?? '',
      title: contentParts[0] || line,
      contentHtml: decodeAgendaRichContent(encodedContent),
      location: contentParts.slice(2).filter(Boolean).join('｜'),
    }
  }

  // 历史四字段将“主题”和“嘉宾”合并为两行内容，避免升级编辑器时丢失信息。
  const legacyContent = contentParts.length >= 4
    ? [contentParts[1], contentParts[2]].filter(Boolean).join('\n')
    : contentParts[1] ?? ''
  return {
    id: `agenda-entry-${index}`,
    kind: 'entry',
    startTime: timeMatch?.[1] ?? '',
    endTime: timeMatch?.[2] ?? '',
    title: contentParts[0] || line,
    contentHtml: agendaPlainTextToHtml(legacyContent),
    location: contentParts.length >= 4
      ? contentParts.slice(3).filter(Boolean).join('｜')
      : contentParts.slice(2).filter(Boolean).join('｜'),
  }
}

/**
 * 返回当前选中的日期分组，并在选择无效时回退到第一组。
 *
 * 入参：无；函数读取 activeAgendaDateId 和解析后的 agendaGroups。
 * 返回值：AgendaDateGroup | undefined：存在日程时返回当前分组，否则返回 undefined。
 * 异常：当前函数不主动抛出异常。
 */
function buildActiveAgendaGroup(): AgendaDateGroup | undefined {
  return agendaGroups.value.find((group) => group.id === activeAgendaDateId.value) ?? agendaGroups.value[0]
}

/**
 * 生成当前日期的时间范围摘要。
 *
 * 入参：无；函数读取当前激活日期分组。
 * 返回值：string：形如“全天 09:00–17:00”的摘要；无时间时返回当日日程说明。
 * 异常：当前函数不主动抛出异常。
 */
function buildAgendaSummary(): string {
  const entries = activeAgendaGroup.value?.items.filter((item): item is AgendaEntryItem => item.kind === 'entry') ?? []
  if (!entries.length) {
    return '当日安排正在准备中'
  }
  const firstTime = entries.find((item) => item.startTime)?.startTime ?? ''
  const lastTimedEntry = [...entries].reverse().find((item) => item.endTime || item.startTime)
  const lastTime = lastTimedEntry?.endTime || lastTimedEntry?.startTime || ''
  if (firstTime && firstTime === lastTime) {
    return `${firstTime} 开始`
  }
  const timeRange = firstTime && lastTime ? `${firstTime}–${lastTime}` : firstTime || lastTime
  return timeRange ? `全天 ${timeRange}` : '当日日程'
}

/**
 * 在日程加载后选择最适合嘉宾查看的默认日期。
 *
 * 入参：无；函数读取浏览器当前日期与解析后的 agendaGroups。
 * 返回值：void；函数更新 activeAgendaDateId，不返回业务数据。
 * 异常：当前函数不主动抛出异常；没有当天分组时选择第一个日期。
 */
function selectDefaultAgendaDate(): void {
  const now = new Date()
  const monthDay = `${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  const fullDate = `${now.getFullYear()}-${monthDay}`
  const defaultGroup = agendaGroups.value.find(
    (group) => group.dateKey === fullDate || group.dateKey === monthDay,
  ) ?? agendaGroups.value[0]
  activeAgendaDateId.value = defaultGroup?.id ?? ''
}

/**
 * 将其他会议助手功能的正文按空行分隔为内容卡片。
 *
 * 入参：无；函数读取当前功能正文。
 * 返回值：string[]：清理空白后的内容区块；正文为空时返回占位提示。
 * 异常：当前函数不主动抛出异常。
 */
function buildContentBlocks(): string[] {
  const blocks = feature.value?.content.split(/\n\s*\n/).map((block) => block.trim()).filter(Boolean) ?? []
  return blocks.length ? blocks : ['内容待补充。']
}

/**
 * 根据管理员确认的高德坐标生成手机导航链接。
 *
 * 入参：无；函数读取会议导航名称、经度和纬度。
 * 返回值：string：可调起高德地图或打开高德 H5 的 URI；坐标缺失时返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
function buildNavigationUrl(): string {
  const longitude = meeting.value?.navigationLongitude
  const latitude = meeting.value?.navigationLatitude
  if (longitude === undefined || latitude === undefined) {
    return ''
  }
  const params = new URLSearchParams({
    from: '',
    to: `${longitude},${latitude},${meeting.value?.navigationName || meeting.value?.location || '会议地点'}`,
    mode: 'car',
    policy: '0',
    src: 'zhihui',
    callnative: '1',
  })
  return `https://uri.amap.com/navigation?${params.toString()}`
}

/**
 * 将和风天气图标代码转换为当前页面使用的简洁天气符号。
 *
 * 入参：iconCode 为和风天气图标代码，必填。
 * 返回值：string：晴、云、雨、雪、雷或雾对应的 Emoji（表情符号）。
 * 异常：未知代码返回通用多云图标，不向页面抛出异常。
 */
function weatherIcon(iconCode: string): string {
  const code = Number(iconCode)
  if (code === 100 || code === 150) return '☀️'
  if (code >= 101 && code <= 104) return '⛅'
  if (code >= 300 && code <= 399) return code >= 302 && code <= 304 ? '⛈️' : '🌧️'
  if (code >= 400 && code <= 499) return '🌨️'
  if (code >= 500 && code <= 515) return '🌫️'
  return '☁️'
}

/**
 * 将供应商 ISO 日期格式化为中文月日与星期。
 *
 * 入参：value 为 `yyyy-MM-dd` 日期文本，必填。
 * 返回值：string：形如“7月16日 周四”的本地日期文本。
 * 异常：日期无效时返回原始文本。
 */
function formatForecastDate(value: string): string {
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  const weekdayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${date.getMonth() + 1}月${date.getDate()}日 ${weekdayNames[date.getDay()]}`
}

/**
 * 返回当前本地日期对应的和风日期键（yyyy-MM-dd），用于当日预报标记。
 *
 * 入参：无。
 * 返回值：string：当前日期字符串，与和风天气返回的 daily.date 字段格式一致。
 * 异常：当前函数不主动抛出异常。
 */
const todayKey = computed(computeTodayKey)

function computeTodayKey(): string {
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

/**
 * 判断给定的和风日期键是否为今天。
 *
 * 入参：value 为日期键，必填。
 * 返回值：boolean：与今日日期一致返回 true，否则返回 false。
 * 异常：当前函数不主动抛出异常。
 */
function isToday(value: string): boolean {
  return value === todayKey.value
}

/**
 * 将日期键简化为"7/16"格式。
 *
 * 入参：value 为 yyyy-MM-dd 格式的日期键，必填。
 * 返回值：string：形如"7/16"的短日期；日期无效时返回原文本。
 * 异常：当前函数不主动抛出异常。
 */
function formatForecastShort(value: string): string {
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  return `${date.getMonth() + 1}/${date.getDate()}`
}

/**
 * 从日期键返回中文星期文本。
 *
 * 入参：value 为 yyyy-MM-dd 格式的日期键，必填。
 * 返回值：string：周一至周日；日期无效时返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
function formatWeekday(value: string): string {
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return ''
  return ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][date.getDay()]
}

/**
 * 把和风天气 obsTime 字段（ISO 字符串）转换为当日"HH:mm"。
 *
 * 入参：value 为 ISO 时间字符串（如 2026-07-16T12:00+08:00），必填。
 * 返回值：string：形如"12:30"的简短时间；解析失败时返回原始字符串。
 * 异常：当前函数不主动抛出异常。
 */
function formatObservedAt(value: string): string {
  const normalized = value.includes('T') && !value.includes('+') && !value.includes('Z') ? `${value}+08:00` : value
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) return value
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

/**
 * 把和风天气 fxTime 字段（ISO 字符串）转换为"周X HH:mm"，便于展示未来几小时。
 *
 * 入参：value 为 ISO 时间字符串，必填。
 * 返回值：string：形如"今天 14:00"或"周二 14:00"；解析失败时返回原始字符串。
 * 异常：当前函数不主动抛出异常。
 */
function formatHourlyTime(value: string): string {
  const normalized = value.includes('T') && !value.includes('+') && !value.includes('Z') ? `${value}+08:00` : value
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) return value
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const time = `${hours}:${minutes}`
  const now = new Date()
  if (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  ) {
    return `今天 ${time}`
  }
  const weekdayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${weekdayNames[date.getDay()]} ${time}`
}

onMounted(loadFeature)
</script>
