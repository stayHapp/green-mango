<template>
  <div class="material-rich-editor">
    <div class="material-rich-editor__toolbar" aria-label="资料内容格式">
      <button type="button" aria-label="加粗" title="加粗" @mousedown.prevent="applyFormat('bold')">
        <strong>B</strong>
      </button>
      <span aria-hidden="true"></span>
      <button
        type="button"
        aria-label="项目符号列表"
        title="项目符号列表"
        @mousedown.prevent="applyFormat('insertUnorderedList')"
      >
        • 列表
      </button>
      <button
        type="button"
        aria-label="编号列表"
        title="编号列表"
        @mousedown.prevent="applyFormat('insertOrderedList')"
      >
        1. 列表
      </button>
      <span aria-hidden="true"></span>
      <button
        type="button"
        aria-label="首行缩进2字符"
        title="首行缩进2字符"
        @mousedown.prevent="toggleFirstLineIndent"
      >
        首行缩进
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
      class="material-rich-editor__content"
      contenteditable="true"
      role="textbox"
      aria-multiline="true"
      :aria-label="label"
      data-placeholder="输入资料内容，可使用段落、加粗、列表和缩进"
      @click="captureActiveParagraph"
      @keyup="captureActiveParagraph"
      @input="handleEditorInput"
      @blur="normalizeEditorValue"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import {
  MATERIAL_FIRST_LINE_INDENT_CLASS,
  sanitizeMaterialRichHtml,
} from '../utils/materialRichText'

type MaterialFormatCommand =
  | 'bold'
  | 'insertUnorderedList'
  | 'insertOrderedList'
  | 'indent'
  | 'outdent'

const props = defineProps<{
  modelValue: string
  label: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const editorElement = ref<HTMLElement>()
const activeParagraph = ref<HTMLElement>()

watch(getModelValue, synchronizeEditorValue)
onMounted(initializeEditorValue)

/**
 * 获取父组件传入的会议资料文档 HTML。
 *
 * 入参：无；读取必填 modelValue 属性。
 * 返回值：string：当前编辑器文档 HTML。
 * 异常：当前函数不主动抛出异常。
 */
function getModelValue(): string {
  return props.modelValue
}

/**
 * 在编辑器挂载后写入经过清洗的初始文档内容。
 *
 * 入参：无。
 * 返回值：void：更新可编辑区域但不发送表单变更事件。
 * 异常：编辑区域尚未挂载时不执行。
 */
function initializeEditorValue(): void {
  if (editorElement.value) {
    editorElement.value.innerHTML = sanitizeMaterialRichHtml(props.modelValue)
  }
}

/**
 * 响应父组件内容变化并避免覆盖正在编辑的等价内容。
 *
 * 入参：value 为必填新文档 HTML。
 * 返回值：void：外部内容确有变化时同步编辑区域。
 * 异常：编辑区域尚未挂载时不执行。
 */
function synchronizeEditorValue(value: string): void {
  const editor = editorElement.value
  if (!editor) {
    return
  }
  const safeValue = sanitizeMaterialRichHtml(value)
  if (sanitizeMaterialRichHtml(editor.innerHTML) !== safeValue) {
    editor.innerHTML = safeValue
  }
}

/**
 * 将编辑区域当前内容清洗后发送给父组件。
 *
 * 入参：无；读取可编辑区域 innerHTML。
 * 返回值：void：通过 v-model 事件发送白名单文档 HTML。
 * 异常：编辑区域不存在时不执行。
 */
function emitEditorValue(): void {
  if (editorElement.value) {
    emit('update:modelValue', sanitizeMaterialRichHtml(editorElement.value.innerHTML))
  }
}

/**
 * 在编辑器输入后记录当前段落并同步安全内容。
 *
 * 入参：event 为必填编辑器输入事件。
 * 返回值：void：更新最后活动段落并向父组件发送文档 HTML。
 * 异常：当前函数不主动抛出异常。
 */
function handleEditorInput(event: Event): void {
  captureActiveParagraph(event)
  emitEditorValue()
}

/**
 * 记录光标或点击目标所在的最后活动段落。
 *
 * 入参：event 为可选编辑器事件，用于在浏览器选区未落到文本节点时提供目标元素回退。
 * 返回值：void：找到编辑器内 `p` 或 `div` 段落时保存元素引用。
 * 异常：选区和事件目标都不在有效段落内时不执行。
 */
function captureActiveParagraph(event?: Event): void {
  const editor = editorElement.value
  if (!editor) {
    return
  }
  const selectionNode = document.getSelection()?.anchorNode
  const selectionElement = selectionNode?.nodeType === Node.ELEMENT_NODE
    ? selectionNode as HTMLElement
    : selectionNode?.parentElement
  const eventElement = event?.target instanceof HTMLElement ? event.target : undefined
  // 鼠标点击时优先采用事件目标，避免浏览器在 click 事件中仍返回上一次选区。
  const paragraph = findEditorParagraph(eventElement, editor)
    ?? findEditorParagraph(selectionElement, editor)
  if (paragraph) {
    activeParagraph.value = paragraph
  }
}

/**
 * 从候选元素向上查找编辑器内的有效段落。
 *
 * 入参：element 为可选候选元素；editor 为必填资料编辑区域。
 * 返回值：HTMLElement | undefined：返回编辑器内且不等于编辑器根节点的 `p` 或 `div` 段落。
 * 异常：候选元素不存在或不属于编辑器时返回 undefined，不主动抛出异常。
 */
function findEditorParagraph(
  element: HTMLElement | undefined | null,
  editor: HTMLElement,
): HTMLElement | undefined {
  const paragraph = element?.closest<HTMLElement>('p, div')
  return paragraph && paragraph !== editor && editor.contains(paragraph)
    ? paragraph
    : undefined
}

/**
 * 在编辑器失焦时规范化 DOM 并同步最终安全内容。
 *
 * 入参：无。
 * 返回值：void：清理编辑区域并发送规范化 HTML。
 * 异常：编辑区域不存在时不执行。
 */
function normalizeEditorValue(): void {
  if (!editorElement.value) {
    return
  }
  const safeValue = sanitizeMaterialRichHtml(editorElement.value.innerHTML)
  editorElement.value.innerHTML = safeValue
  emit('update:modelValue', safeValue)
}

/**
 * 对当前资料编辑选区执行受限文档格式命令。
 *
 * 入参：command 为必填格式命令，只允许加粗、项目符号、编号、增加缩进或减少缩进。
 * 返回值：void：命令完成后立即同步安全内容。
 * 异常：浏览器不支持命令时不主动抛出异常，原内容保持不变。
 */
function applyFormat(command: MaterialFormatCommand): void {
  const editor = editorElement.value
  if (!editor) {
    return
  }
  editor.focus()
  document.execCommand(command, false)
  emitEditorValue()
}

/**
 * 切换光标所在段落的中文文档首行缩进。
 *
 * 入参：无；函数读取当前编辑器选区所在的 `p` 或 `div` 段落。
 * 返回值：void：为当前段落添加或移除固定首行缩进类，并同步 2 字符缩进格式。
 * 异常：选区不在资料编辑器段落内时不执行，不主动抛出异常。
 */
function toggleFirstLineIndent(): void {
  const editor = editorElement.value
  const selection = document.getSelection()
  const anchorNode = selection?.anchorNode
  if (!editor) {
    return
  }
  const anchorElement = anchorNode?.nodeType === Node.ELEMENT_NODE
    ? anchorNode as HTMLElement
    : anchorNode?.parentElement
  const selectedParagraph = anchorNode && editor.contains(anchorNode)
    ? findEditorParagraph(anchorElement, editor)
    : undefined
  // 工具栏会改变浏览器选区，优先使用点击或键盘事件刚记录的活动段落。
  const paragraph = activeParagraph.value ?? selectedParagraph
  if (!paragraph || !editor.contains(paragraph)) {
    return
  }
  paragraph.classList.toggle(MATERIAL_FIRST_LINE_INDENT_CLASS)
  emitEditorValue()
  editor.focus()
}
</script>

<style scoped>
.material-rich-editor {
  width: 100%;
  overflow: hidden;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  background: #ffffff;
  transition: border-color 160ms ease, box-shadow 160ms ease;
}

.material-rich-editor:focus-within {
  border-color: #08724e;
  box-shadow: 0 0 0 2px rgba(8, 114, 78, 0.1);
}

.material-rich-editor__toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 3px;
  min-height: 38px;
  border-bottom: 1px solid #edf0ee;
  background: #f8faf9;
  padding: 4px 7px;
}

.material-rich-editor__toolbar > span {
  width: 1px;
  height: 18px;
  margin: 0 3px;
  background: #dfe6e2;
}

.material-rich-editor__toolbar button {
  min-height: 28px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: #40554a;
  padding: 3px 8px;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.material-rich-editor__toolbar button:hover,
.material-rich-editor__toolbar button:focus-visible {
  background: #e8f3ed;
  color: #07583f;
  outline: none;
}

.material-rich-editor__content {
  min-height: 220px;
  max-height: 420px;
  overflow: auto;
  color: #263c31;
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.75;
  text-align: justify;
  text-justify: inter-ideograph;
  outline: none;
}

.material-rich-editor__content:empty::before {
  color: #a8abb2;
  content: attr(data-placeholder);
  pointer-events: none;
}

.material-rich-editor__content :deep(p),
.material-rich-editor__content :deep(div) {
  margin: 0 0 0.7em;
}

.material-rich-editor__content :deep(.material-first-line-indent) {
  text-indent: 2em;
}

.material-rich-editor__content :deep(ul),
.material-rich-editor__content :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.8em;
}

.material-rich-editor__content :deep(li + li) {
  margin-top: 0.25em;
}

.material-rich-editor__content :deep(blockquote) {
  margin: 0.5em 0 0.5em 1.5em;
  border-left: 2px solid #cddbd4;
  padding-left: 0.9em;
}
</style>
