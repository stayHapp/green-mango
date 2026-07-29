<template>
  <div class="agenda-rich-editor">
    <div class="agenda-rich-editor__toolbar" aria-label="内容格式">
      <button type="button" aria-label="加粗" title="加粗" @mousedown.prevent="applyFormat('bold')">
        <strong>B</strong>
      </button>
      <button type="button" aria-label="增加缩进" title="增加缩进" @mousedown.prevent="applyFormat('indent')">
        增加缩进
      </button>
      <button type="button" aria-label="减少缩进" title="减少缩进" @mousedown.prevent="applyFormat('outdent')">
        减少缩进
      </button>
    </div>
    <div
      ref="editorElement"
      class="agenda-rich-editor__content"
      contenteditable="true"
      role="textbox"
      aria-multiline="true"
      :aria-label="label"
      data-placeholder="输入内容，可换行并设置加粗或缩进"
      @input="emitEditorValue"
      @blur="normalizeEditorValue"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { sanitizeAgendaRichHtml } from '../utils/agendaRichText'

const props = defineProps<{
  modelValue: string
  label: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const editorElement = ref<HTMLElement>()

watch(getModelValue, synchronizeEditorValue)
onMounted(initializeEditorValue)

/**
 * 获取父组件传入的富文本内容。
 *
 * 入参：无；函数读取必填的 modelValue 属性。
 * 返回值：string：当前富文本 HTML。
 * 异常：当前函数不主动抛出异常。
 */
function getModelValue(): string {
  return props.modelValue
}

/**
 * 在组件挂载后写入经过清洗的初始富文本。
 *
 * 入参：无。
 * 返回值：void；函数更新可编辑区域，不发送变更事件。
 * 异常：当前函数不主动抛出异常；编辑区域尚未挂载时不执行。
 */
function initializeEditorValue(): void {
  if (editorElement.value) {
    editorElement.value.innerHTML = sanitizeAgendaRichHtml(props.modelValue)
  }
}

/**
 * 响应父组件的外部内容变化，并避免覆盖正在编辑的等价内容。
 *
 * 入参：value 为必填的新富文本 HTML。
 * 返回值：void；必要时更新可编辑区域。
 * 异常：当前函数不主动抛出异常。
 */
function synchronizeEditorValue(value: string): void {
  const editor = editorElement.value
  if (!editor) {
    return
  }
  const safeValue = sanitizeAgendaRichHtml(value)
  if (sanitizeAgendaRichHtml(editor.innerHTML) !== safeValue) {
    editor.innerHTML = safeValue
  }
}

/**
 * 将编辑区域当前内容清洗后发送给父组件。
 *
 * 入参：无；函数读取可编辑区域的 innerHTML。
 * 返回值：void；通过 v-model 事件发送安全 HTML。
 * 异常：当前函数不主动抛出异常；编辑区域不存在时不执行。
 */
function emitEditorValue(): void {
  if (!editorElement.value) {
    return
  }
  emit('update:modelValue', sanitizeAgendaRichHtml(editorElement.value.innerHTML))
}

/**
 * 在编辑器失焦时清理 DOM，并让界面与持久化内容保持一致。
 *
 * 入参：无。
 * 返回值：void；更新编辑区域并发送清洗后的 HTML。
 * 异常：当前函数不主动抛出异常。
 */
function normalizeEditorValue(): void {
  if (!editorElement.value) {
    return
  }
  const safeValue = sanitizeAgendaRichHtml(editorElement.value.innerHTML)
  editorElement.value.innerHTML = safeValue
  emit('update:modelValue', safeValue)
}

/**
 * 对当前选区执行受限富文本命令。
 *
 * 入参：command 为必填格式命令，仅允许 bold、indent 或 outdent。
 * 返回值：void；执行命令后立即同步清洗结果。
 * 异常：浏览器不支持命令时不主动抛出异常，内容保持不变。
 */
function applyFormat(command: 'bold' | 'indent' | 'outdent'): void {
  const editor = editorElement.value
  if (!editor) {
    return
  }
  editor.focus()
  document.execCommand(command, false)
  emitEditorValue()
}
</script>

<style scoped>
.agenda-rich-editor {
  min-width: 260px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #ffffff;
  transition: border-color 160ms ease, box-shadow 160ms ease;
}

.agenda-rich-editor:focus-within {
  border-color: #08724e;
  box-shadow: 0 0 0 2px rgba(8, 114, 78, 0.1);
}

.agenda-rich-editor__toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  min-height: 30px;
  border-bottom: 1px solid #edf0ee;
  background: #f8faf9;
  padding: 2px 5px;
}

.agenda-rich-editor__toolbar button {
  min-height: 24px;
  border: 0;
  border-radius: 3px;
  background: transparent;
  color: #40554a;
  padding: 2px 7px;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.agenda-rich-editor__toolbar button:hover,
.agenda-rich-editor__toolbar button:focus-visible {
  background: #e8f3ed;
  color: #07583f;
  outline: none;
}

.agenda-rich-editor__content {
  min-height: 78px;
  max-height: 180px;
  overflow: auto;
  color: #263c31;
  padding: 8px 10px;
  font-size: 13px;
  line-height: 1.55;
  outline: none;
  white-space: normal;
}

.agenda-rich-editor__content:empty::before {
  color: #a8abb2;
  content: attr(data-placeholder);
  pointer-events: none;
}

.agenda-rich-editor__content :deep(div),
.agenda-rich-editor__content :deep(p) {
  margin: 0;
}

.agenda-rich-editor__content :deep(blockquote) {
  margin: 0 0 0 1.5em;
}
</style>
