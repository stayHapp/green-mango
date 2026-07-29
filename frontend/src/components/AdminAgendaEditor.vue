<template>
  <section class="agenda-editor">
    <aside class="agenda-editor__days" aria-label="会议日期">
      <div class="agenda-editor__side-heading">
        <strong>会议日期</strong>
        <small>按天组织日程</small>
      </div>
      <div class="agenda-editor__day-list" role="tablist" aria-label="选择编辑日期">
        <button
          v-for="day in days"
          :key="day.key"
          type="button"
          role="tab"
          :aria-selected="selectedDay?.key === day.key"
          :class="{ 'is-active': selectedDay?.key === day.key }"
          @click="selectDay(day.key)"
        >
          <strong>{{ formatEditorDayLabel(day.date) }}</strong>
          <span>{{ day.periods.length }} 个时段</span>
        </button>
      </div>
      <el-button class="agenda-editor__add-day" plain type="primary" :icon="Plus" @click="addDay">新增日期</el-button>
    </aside>

    <div v-if="selectedDay" class="agenda-editor__main">
      <header class="agenda-editor__day-toolbar">
        <label>
          <span>当前日期</span>
          <el-date-picker
            v-model="selectedDay.date"
            type="date"
            value-format="YYYY-MM-DD"
            format="YYYY年MM月DD日"
            placeholder="选择会议日期"
            :clearable="false"
          />
        </label>
        <el-button plain type="danger" :icon="Delete" @click="removeSelectedDay">删除日期</el-button>
      </header>

      <div class="agenda-editor__periods">
        <section v-for="(period, periodIndex) in selectedDay.periods" :key="period.key" class="agenda-period">
          <header class="agenda-period__header">
            <el-select v-model="period.period" class="agenda-period__type" aria-label="时段">
              <el-option v-for="option in periodOptions" :key="option" :label="option" :value="option" />
            </el-select>
            <el-input v-model="period.title" class="agenda-period__title" placeholder="填写本时段主题，例如：开幕致辞与主旨演讲" />
            <div class="agenda-period__actions">
              <el-button
                text
                :icon="ArrowUp"
                :disabled="periodIndex === 0"
                aria-label="上移时段"
                @click="movePeriod(periodIndex, -1)"
              />
              <el-button
                text
                :icon="ArrowDown"
                :disabled="periodIndex === selectedDay.periods.length - 1"
                aria-label="下移时段"
                @click="movePeriod(periodIndex, 1)"
              />
              <el-button text type="danger" :icon="Delete" aria-label="删除时段" @click="removePeriod(periodIndex)" />
            </div>
          </header>

          <div class="agenda-period__entry-head" aria-hidden="true">
            <span>时间段</span>
            <span>环节</span>
            <span>内容</span>
            <span>地点</span>
            <span>操作</span>
          </div>

          <div class="agenda-period__entries">
            <article v-for="(entry, entryIndex) in period.entries" :key="entry.key" class="agenda-entry-editor">
              <div class="agenda-entry-editor__time-range">
                <el-time-select
                  v-model="entry.startTime"
                  start="06:00"
                  step="00:10"
                  end="23:50"
                  placeholder="开始"
                  :aria-label="`第 ${entryIndex + 1} 个环节开始时间`"
                />
                <span>至</span>
                <el-time-select
                  v-model="entry.endTime"
                  start="06:00"
                  step="00:10"
                  end="23:50"
                  placeholder="结束"
                  :aria-label="`第 ${entryIndex + 1} 个环节结束时间`"
                />
              </div>
              <el-input v-model="entry.title" placeholder="主题演讲" :aria-label="`第 ${entryIndex + 1} 个环节名称`" />
              <AgendaRichTextEditor
                v-model="entry.content"
                :label="`第 ${entryIndex + 1} 个环节内容`"
              />
              <el-input v-model="entry.location" placeholder="主会场" :aria-label="`第 ${entryIndex + 1} 个环节地点`" />
              <div class="agenda-entry-editor__actions">
                <el-button text :icon="CopyDocument" aria-label="复制环节" @click="duplicateEntry(periodIndex, entryIndex)" />
                <el-button text type="danger" :icon="Delete" aria-label="删除环节" @click="removeEntry(periodIndex, entryIndex)" />
              </div>
            </article>
          </div>

          <el-button class="agenda-period__add-entry" plain :icon="Plus" @click="addEntry(periodIndex)">新增环节</el-button>
        </section>
      </div>

      <el-button class="agenda-editor__add-period" plain type="primary" :icon="Plus" @click="addPeriod">新增时段</el-button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowDown, ArrowUp, CopyDocument, Delete, Plus } from '@element-plus/icons-vue'
import AgendaRichTextEditor from './AgendaRichTextEditor.vue'
import {
  agendaPlainTextToHtml,
  decodeAgendaRichContent,
  encodeAgendaRichContent,
  isEncodedAgendaRichContent,
} from '../utils/agendaRichText'

interface AgendaEditorEntry {
  key: string
  startTime: string
  endTime: string
  title: string
  content: string
  location: string
}

interface AgendaEditorPeriod {
  key: string
  period: string
  title: string
  entries: AgendaEditorEntry[]
}

interface AgendaEditorDay {
  key: string
  date: string
  periods: AgendaEditorPeriod[]
}

interface AgendaDateParts {
  year: number
  month: number
  day: number
  period: string
}

const props = defineProps<{
  modelValue: string
  meetingStartTime?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const periodOptions = ['上午', '中午', '下午', '晚上', '全天']
let editorKeySequence = 0
const days = ref<AgendaEditorDay[]>(parseAgendaContent(props.modelValue))
const activeDayKey = ref(days.value[0]?.key ?? '')
const selectedDay = computed(getSelectedDay)

watch(getModelValue, synchronizeFromModel)
watch(days, emitSerializedContent, { deep: true })

/**
 * 获取父组件传入的原始日程正文，供监听器判断外部内容变化。
 *
 * 入参：无；函数读取必填的 modelValue 属性。
 * 返回值：string：当前父组件持有的日程正文。
 * 异常：当前函数不主动抛出异常。
 */
function getModelValue(): string {
  return props.modelValue
}

/**
 * 生成编辑器内部对象使用的稳定唯一键。
 *
 * 入参：prefix 为必填的键前缀，用于区分日期、时段和环节。
 * 返回值：string：当前组件实例内不重复的键。
 * 异常：当前函数不主动抛出异常。
 */
function createEditorKey(prefix: string): string {
  editorKeySequence += 1
  return `${prefix}-${editorKeySequence}`
}

/**
 * 返回会议开始年份，用于把缺少年份的历史日程转换为日期选择器值。
 *
 * 入参：无；函数读取可选的 meetingStartTime 属性。
 * 返回值：number：合法会议年份；缺失或格式无效时返回当前年份。
 * 异常：当前函数不主动抛出异常。
 */
function getMeetingYear(): number {
  const yearText = props.meetingStartTime?.slice(0, 4) ?? ''
  const year = Number(yearText)
  return Number.isInteger(year) && year >= 2000 && year <= 2200 ? year : new Date().getFullYear()
}

/**
 * 创建空白环节，并允许复制已有环节的部分字段。
 *
 * 入参：partial 为可选初始字段；所有字段均为可选字符串。
 * 返回值：AgendaEditorEntry：带稳定键且字段完整的可编辑环节。
 * 异常：当前函数不主动抛出异常。
 */
function createEmptyEntry(partial?: Partial<Omit<AgendaEditorEntry, 'key'>>): AgendaEditorEntry {
  return {
    key: createEditorKey('entry'),
    startTime: partial?.startTime ?? '',
    endTime: partial?.endTime ?? '',
    title: partial?.title ?? '',
    content: partial?.content ?? '',
    location: partial?.location ?? '',
  }
}

/**
 * 创建空白时段，并允许指定时段名称、主题和初始环节。
 *
 * 入参：partial 为可选初始字段；period、title 和 entries 均可省略。
 * 返回值：AgendaEditorPeriod：至少包含一个空白环节的时段。
 * 异常：当前函数不主动抛出异常。
 */
function createEmptyPeriod(partial?: Partial<Omit<AgendaEditorPeriod, 'key'>>): AgendaEditorPeriod {
  return {
    key: createEditorKey('period'),
    period: partial?.period ?? '上午',
    title: partial?.title ?? '',
    entries: partial?.entries !== undefined ? partial.entries : [createEmptyEntry()],
  }
}

/**
 * 创建空白日期，并使用会议开始日期或当前日期作为默认值。
 *
 * 入参：date 为可选的 `YYYY-MM-DD` 日期字符串。
 * 返回值：AgendaEditorDay：包含一个默认时段的日期对象。
 * 异常：当前函数不主动抛出异常；无效日期仍作为原字符串交给日期组件处理。
 */
function createEmptyDay(date?: string): AgendaEditorDay {
  const fallbackDate = props.meetingStartTime?.slice(0, 10) || formatDateKey(new Date())
  return {
    key: createEditorKey('day'),
    date: date || fallbackDate,
    periods: [createEmptyPeriod()],
  }
}

/**
 * 把日期对象转换为日期选择器使用的 `YYYY-MM-DD` 字符串。
 *
 * 入参：date 为必填的 Date 对象。
 * 返回值：string：按本地年月日组成的日期键。
 * 异常：当前函数不主动抛出异常。
 */
function formatDateKey(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * 解析日期标题行，兼容中文日期和数字分隔日期。
 *
 * 入参：line 为必填的非空正文行。
 * 返回值：AgendaDateParts | null：识别成功返回年月日和可选时段，否则返回 null。
 * 异常：当前函数不主动抛出异常；月份或日期越界时返回 null。
 * 使用示例：`8月18日（周二）上午` 会使用会议年份并返回上午时段。
 */
function parseAgendaDateLine(line: string): AgendaDateParts | null {
  const chineseMatch = line.match(
    /^(?:(\d{4})\s*年\s*)?(\d{1,2})\s*月\s*(\d{1,2})\s*日?\s*(?:[（(]?\s*周[一二三四五六日天]\s*[）)]?)?\s*(上午|中午|下午|晚上|全天)?$/,
  )
  const numericMatch = line.match(
    /^(?:(\d{4})\s*[-/.]\s*)?(\d{1,2})\s*[-/.]\s*(\d{1,2})\s*(?:[（(]?\s*周[一二三四五六日天]\s*[）)]?)?\s*(上午|中午|下午|晚上|全天)?$/,
  )
  const match = chineseMatch ?? numericMatch
  if (!match) {
    return null
  }
  const year = Number(match[1] || getMeetingYear())
  const month = Number(match[2])
  const day = Number(match[3])
  if (month < 1 || month > 12 || day < 1 || day > 31) {
    return null
  }
  return { year, month, day, period: match[4] ?? '' }
}

/**
 * 将持久化的纯文本日程转换为后台结构化编辑对象。
 *
 * 入参：content 为必填字符串，可为空，也可包含历史三段式、四段式或新版富文本环节。
 * 返回值：AgendaEditorDay[]：至少包含一个可编辑日期的结构化日程。
 * 异常：当前函数不主动抛出异常；无法识别的正文作为普通环节名称保留。
 * 使用示例：`09:00-09:30 主题演讲｜rich:...｜主会场` 会拆分为时间段、环节、内容和地点。
 */
function parseAgendaContent(content: string): AgendaEditorDay[] {
  const lines = content.split('\n').map((line) => line.trim()).filter(Boolean)
  if (!lines.length) {
    return [createEmptyDay()]
  }

  const parsedDays: AgendaEditorDay[] = []
  let currentDay: AgendaEditorDay | undefined
  let currentPeriod: AgendaEditorPeriod | undefined

  lines.forEach((line) => {
    const dateParts = parseAgendaDateLine(line)
    if (dateParts) {
      const month = String(dateParts.month).padStart(2, '0')
      const day = String(dateParts.day).padStart(2, '0')
      currentDay = {
        key: createEditorKey('day'),
        date: `${dateParts.year}-${month}-${day}`,
        periods: [],
      }
      parsedDays.push(currentDay)
      currentPeriod = undefined
      if (dateParts.period) {
        currentPeriod = createEmptyPeriod({ period: dateParts.period, entries: [] })
        currentDay.periods.push(currentPeriod)
      }
      return
    }

    if (!currentDay) {
      currentDay = {
        key: createEditorKey('day'),
        date: props.meetingStartTime?.slice(0, 10) || formatDateKey(new Date()),
        periods: [],
      }
      parsedDays.push(currentDay)
    }

    const periodMatch = line.match(/^(上午|中午|下午|晚上|全天)(?:\s*[|｜]\s*(.+))?$/)
    if (periodMatch) {
      currentPeriod = createEmptyPeriod({
        period: periodMatch[1],
        title: periodMatch[2]?.trim() ?? '',
        entries: [],
      })
      currentDay.periods.push(currentPeriod)
      return
    }

    if (!currentPeriod) {
      currentPeriod = createEmptyPeriod({ period: '全天', entries: [] })
      currentDay.periods.push(currentPeriod)
    }
    currentPeriod.entries.push(parseAgendaEntryLine(line))
  })

  // 解析后为没有环节的日期或时段补充空行，确保界面始终可继续编辑。
  parsedDays.forEach((day) => {
    if (!day.periods.length) {
      day.periods.push(createEmptyPeriod())
    }
    day.periods.forEach((period) => {
      if (!period.entries.length) {
        period.entries.push(createEmptyEntry())
      }
    })
  })
  return parsedDays
}

/**
 * 解析单条日程正文，兼容历史三段、四段格式和新版富文本格式。
 *
 * 入参：line 为必填的非空日程行。
 * 返回值：AgendaEditorEntry：包含时间段、环节、富文本内容与地点的编辑对象。
 * 异常：当前函数不主动抛出异常；无法识别时间时保留完整正文为环节名称。
 */
function parseAgendaEntryLine(line: string): AgendaEditorEntry {
  const match = line.match(/^(\d{1,2}:\d{2})(?:\s*[-–—~至]\s*(\d{1,2}:\d{2}))?\s*(.*)$/)
  const content = match?.[3]?.trim() || line
  const parts = content.split(/\s*[|｜]\s*/).map((part) => part.trim())
  if (isEncodedAgendaRichContent(parts[1] ?? '')) {
    return createEmptyEntry({
      startTime: match?.[1] ?? '',
      endTime: match?.[2] ?? '',
      title: parts[0],
      content: decodeAgendaRichContent(parts[1]),
      location: parts.slice(2).filter(Boolean).join('｜'),
    })
  }
  if (parts.length >= 4) {
    const legacyContent = [parts[1], parts[2]].filter(Boolean).join('\n')
    return createEmptyEntry({
      startTime: match?.[1] ?? '',
      endTime: match?.[2] ?? '',
      title: parts[0],
      content: agendaPlainTextToHtml(legacyContent),
      location: parts.slice(3).filter(Boolean).join('｜'),
    })
  }
  return createEmptyEntry({
    startTime: match?.[1] ?? '',
    endTime: match?.[2] ?? '',
    title: parts[0] || line,
    content: agendaPlainTextToHtml(parts[1] ?? ''),
    location: parts[2] ?? '',
  })
}

/**
 * 将后台结构化对象序列化为现有 API 接受的兼容纯文本。
 *
 * 入参：agendaDays 为必填日期数组，可以包含尚未填写完整的表单项。
 * 返回值：string：日期、时段和“环节｜富文本内容｜地点”组成的多行正文。
 * 异常：当前函数不主动抛出异常；完全空白的环节不会写入正文。
 */
function serializeAgendaContent(agendaDays: AgendaEditorDay[]): string {
  const lines: string[] = []
  agendaDays.forEach((day) => {
    lines.push(formatSerializedDay(day.date))
    day.periods.forEach((period) => {
      lines.push(period.title.trim() ? `${period.period}｜${period.title.trim()}` : period.period)
      period.entries.forEach((entry) => {
        const hasContent = [
          entry.startTime,
          entry.endTime,
          entry.title,
          entry.content,
          entry.location,
        ].some((value) => value.trim())
        if (!hasContent) {
          return
        }
        const time = entry.startTime
          ? `${entry.startTime}${entry.endTime ? `-${entry.endTime}` : ''} `
          : ''
        const fields = [
          entry.title.trim() || '未命名环节',
          encodeAgendaRichContent(entry.content),
          entry.location.trim(),
        ]
        lines.push(`${time}${fields.join('｜')}`)
      })
    })
  })
  return lines.join('\n')
}

/**
 * 将日期选择器值格式化为带中文星期的持久化日期标题。
 *
 * 入参：dateKey 为必填的 `YYYY-MM-DD` 日期字符串。
 * 返回值：string：形如 `8月18日（周二）` 的标题；无效时返回“日期待定”。
 * 异常：当前函数不主动抛出异常。
 */
function formatSerializedDay(dateKey: string): string {
  const date = new Date(`${dateKey}T00:00:00`)
  if (Number.isNaN(date.getTime())) {
    return '日期待定'
  }
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${date.getMonth() + 1}月${date.getDate()}日（${weekdays[date.getDay()]}）`
}

/**
 * 格式化左侧日期导航显示文字。
 *
 * 入参：dateKey 为必填的 `YYYY-MM-DD` 日期字符串。
 * 返回值：string：形如 `8月18日 周二` 的紧凑标签；无效时返回“日期待定”。
 * 异常：当前函数不主动抛出异常。
 */
function formatEditorDayLabel(dateKey: string): string {
  return formatSerializedDay(dateKey).replace(/[（）]/g, ' ')
}

/**
 * 返回当前选中的日期对象，并在键失效时回退到第一天。
 *
 * 入参：无；函数读取 activeDayKey 和 days。
 * 返回值：AgendaEditorDay | undefined：当前日期；无数据时返回 undefined。
 * 异常：当前函数不主动抛出异常。
 */
function getSelectedDay(): AgendaEditorDay | undefined {
  return days.value.find((day) => day.key === activeDayKey.value) ?? days.value[0]
}

/**
 * 在父组件内容发生外部变化时重新解析编辑器状态。
 *
 * 入参：value 为必填的新正文字符串。
 * 返回值：void；仅在新正文与当前序列化结果不一致时更新本地日期。
 * 异常：当前函数不主动抛出异常。
 */
function synchronizeFromModel(value: string): void {
  if (value === serializeAgendaContent(days.value)) {
    return
  }
  days.value = parseAgendaContent(value)
  activeDayKey.value = days.value[0]?.key ?? ''
}

/**
 * 在结构化表单变化后向父组件发送兼容正文。
 *
 * 入参：value 为必填的最新日期数组。
 * 返回值：void；通过 v-model 事件发送序列化正文。
 * 异常：当前函数不主动抛出异常。
 */
function emitSerializedContent(value: AgendaEditorDay[]): void {
  emit('update:modelValue', serializeAgendaContent(value))
}

/**
 * 选择左侧日期并切换右侧编辑内容。
 *
 * 入参：key 为必填的日期稳定键。
 * 返回值：void；更新当前选择，不修改日程正文。
 * 异常：当前函数不主动抛出异常。
 */
function selectDay(key: string): void {
  activeDayKey.value = key
}

/**
 * 新增会议日期，并默认使用最后一天的次日。
 *
 * 入参：无。
 * 返回值：void；追加日期并切换到新日期。
 * 异常：当前函数不主动抛出异常；最后日期无效时使用会议开始日期。
 */
function addDay(): void {
  const lastDate = days.value.at(-1)?.date
  const fallbackDate = props.meetingStartTime?.slice(0, 10) || formatDateKey(new Date())
  const candidate = new Date(`${lastDate || fallbackDate}T00:00:00`)
  if (!Number.isNaN(candidate.getTime())) {
    candidate.setDate(candidate.getDate() + 1)
  }
  const newDay = createEmptyDay(Number.isNaN(candidate.getTime()) ? undefined : formatDateKey(candidate))
  days.value.push(newDay)
  activeDayKey.value = newDay.key
}

/**
 * 删除当前日期；仅剩一天时重置为空白日期，保证编辑器始终可用。
 *
 * 入参：无。
 * 返回值：void；更新日期数组和当前选择。
 * 异常：当前函数不主动抛出异常。
 */
function removeSelectedDay(): void {
  const index = days.value.findIndex((day) => day.key === selectedDay.value?.key)
  if (index < 0) {
    return
  }
  if (days.value.length === 1) {
    const replacement = createEmptyDay(days.value[0].date)
    days.value = [replacement]
    activeDayKey.value = replacement.key
    return
  }
  days.value.splice(index, 1)
  activeDayKey.value = days.value[Math.min(index, days.value.length - 1)]?.key ?? ''
}

/**
 * 在当前日期末尾新增一个时段。
 *
 * 入参：无。
 * 返回值：void；向当前日期追加默认时段。
 * 异常：当前函数不主动抛出异常；没有当前日期时不执行。
 */
function addPeriod(): void {
  if (!selectedDay.value) {
    return
  }
  const nextPeriod = periodOptions[Math.min(selectedDay.value.periods.length, periodOptions.length - 1)] ?? '上午'
  selectedDay.value.periods.push(createEmptyPeriod({ period: nextPeriod }))
}

/**
 * 调整当前日期中某个时段的前后顺序。
 *
 * 入参：
 * - index：必填，待移动时段的零基索引。
 * - direction：必填，只接受 -1 或 1，分别表示上移或下移。
 * 返回值：void；原地调整当前日期的时段数组。
 * 异常：目标索引越界时不执行，不主动抛出异常。
 */
function movePeriod(index: number, direction: -1 | 1): void {
  const periods = selectedDay.value?.periods
  const targetIndex = index + direction
  if (!periods || targetIndex < 0 || targetIndex >= periods.length) {
    return
  }
  const [period] = periods.splice(index, 1)
  periods.splice(targetIndex, 0, period)
}

/**
 * 删除当前日期中的指定时段；最后一个时段被删除时自动补充空白时段。
 *
 * 入参：index 为必填的零基时段索引。
 * 返回值：void；更新当前日期的时段数组。
 * 异常：索引越界时不执行，不主动抛出异常。
 */
function removePeriod(index: number): void {
  const periods = selectedDay.value?.periods
  if (!periods || index < 0 || index >= periods.length) {
    return
  }
  periods.splice(index, 1)
  if (!periods.length) {
    periods.push(createEmptyPeriod())
  }
}

/**
 * 在指定时段末尾新增空白环节。
 *
 * 入参：periodIndex 为必填的零基时段索引。
 * 返回值：void；向目标时段追加环节。
 * 异常：时段不存在时不执行，不主动抛出异常。
 */
function addEntry(periodIndex: number): void {
  selectedDay.value?.periods[periodIndex]?.entries.push(createEmptyEntry())
}

/**
 * 复制指定环节并插入到原环节之后。
 *
 * 入参：
 * - periodIndex：必填，目标时段的零基索引。
 * - entryIndex：必填，目标环节的零基索引。
 * 返回值：void；复制字段并生成新的稳定键。
 * 异常：目标不存在时不执行，不主动抛出异常。
 */
function duplicateEntry(periodIndex: number, entryIndex: number): void {
  const entries = selectedDay.value?.periods[periodIndex]?.entries
  const source = entries?.[entryIndex]
  if (!entries || !source) {
    return
  }
  entries.splice(entryIndex + 1, 0, createEmptyEntry(source))
}

/**
 * 删除指定环节；目标时段只剩一行时改为重置空白行。
 *
 * 入参：
 * - periodIndex：必填，目标时段的零基索引。
 * - entryIndex：必填，目标环节的零基索引。
 * 返回值：void；更新目标时段的环节数组。
 * 异常：目标不存在时不执行，不主动抛出异常。
 */
function removeEntry(periodIndex: number, entryIndex: number): void {
  const entries = selectedDay.value?.periods[periodIndex]?.entries
  if (!entries || entryIndex < 0 || entryIndex >= entries.length) {
    return
  }
  if (entries.length === 1) {
    entries.splice(0, 1, createEmptyEntry())
    return
  }
  entries.splice(entryIndex, 1)
}
</script>

<style scoped>
.agenda-editor {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  min-height: 520px;
  border: 1px solid #dfe7e2;
  border-radius: 8px;
  overflow: hidden;
  background: #ffffff;
}

.agenda-editor__days {
  display: grid;
  grid-template-rows: auto 1fr auto;
  border-right: 1px solid #e2e9e5;
  background: #f8faf9;
}

.agenda-editor__side-heading {
  display: grid;
  gap: 4px;
  padding: 20px 18px 14px;
}

.agenda-editor__side-heading strong {
  color: #243a2f;
  font-size: 15px;
}

.agenda-editor__side-heading small {
  color: #7a8b82;
  font-size: 12px;
}

.agenda-editor__day-list {
  display: grid;
  align-content: start;
  gap: 6px;
  padding: 0 10px;
}

.agenda-editor__day-list button {
  display: grid;
  gap: 4px;
  min-height: 66px;
  border: 0;
  border-left: 4px solid transparent;
  border-radius: 4px;
  background: transparent;
  color: #32483d;
  cursor: pointer;
  padding: 11px 13px;
  text-align: left;
}

.agenda-editor__day-list button:hover {
  background: #f0f6f2;
}

.agenda-editor__day-list button.is-active {
  border-left-color: #08724e;
  background: #eaf5ee;
  color: #07563f;
}

.agenda-editor__day-list button strong {
  font-size: 14px;
}

.agenda-editor__day-list button span {
  color: #71837a;
  font-size: 12px;
}

.agenda-editor__add-day {
  margin: 14px;
}

.agenda-editor__main {
  min-width: 0;
  padding-bottom: 20px;
}

.agenda-editor__day-toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid #e5ebe8;
  padding: 16px 18px;
}

.agenda-editor__day-toolbar label {
  display: grid;
  gap: 7px;
  color: #3e5147;
  font-size: 13px;
  font-weight: 700;
}

.agenda-editor__periods {
  display: grid;
  gap: 14px;
  padding: 16px 18px;
}

.agenda-period {
  border: 1px solid #dfe7e2;
  border-radius: 6px;
  overflow: hidden;
}

.agenda-period__header {
  display: grid;
  grid-template-columns: 110px minmax(220px, 1fr) auto;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid #e6ece8;
  background: #f7faf8;
  padding: 12px;
}

.agenda-period__actions,
.agenda-entry-editor__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
}

.agenda-period__actions :deep(.el-button + .el-button),
.agenda-entry-editor__actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

.agenda-period__entry-head,
.agenda-entry-editor {
  display: grid;
  grid-template-columns: 250px 140px minmax(260px, 1fr) 120px 64px;
  align-items: start;
  gap: 10px;
}

.agenda-period__entry-head {
  border-bottom: 1px solid #edf1ef;
  color: #718178;
  font-size: 12px;
  font-weight: 700;
  padding: 10px 12px 8px;
}

.agenda-period__entries {
  display: grid;
}

.agenda-entry-editor {
  border-bottom: 1px solid #edf1ef;
  padding: 10px 12px;
}

.agenda-entry-editor__time-range {
  display: grid;
  grid-template-columns: minmax(88px, 1fr) auto minmax(88px, 1fr);
  align-items: center;
  gap: 5px;
}

.agenda-entry-editor__time-range > span {
  color: #809087;
  font-size: 12px;
  text-align: center;
}

.agenda-entry-editor__time-range :deep(.el-select) {
  min-width: 0;
  width: 100%;
}

.agenda-entry-editor__time-range :deep(.el-select__wrapper) {
  padding-right: 7px;
  padding-left: 7px;
}

.agenda-entry-editor:last-child {
  border-bottom: 0;
}

.agenda-period__add-entry {
  margin: 12px;
}

.agenda-editor__add-period {
  margin-left: 18px;
}

@media (max-width: 900px) {
  .agenda-editor {
    grid-template-columns: 1fr;
  }

  .agenda-editor__days {
    grid-template-columns: 1fr auto;
    grid-template-rows: auto auto;
    border-right: 0;
    border-bottom: 1px solid #e2e9e5;
  }

  .agenda-editor__day-list {
    grid-column: 1 / -1;
    grid-row: 2;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    padding-bottom: 12px;
  }

  .agenda-editor__add-day {
    align-self: center;
  }

  .agenda-period {
    overflow-x: auto;
  }

  .agenda-period__entry-head,
  .agenda-entry-editor {
    min-width: 880px;
  }
}
</style>
