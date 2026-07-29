const MATERIAL_RICH_CONTENT_PREFIX = 'material-rich:'
// 固定类名只表达中文文档首行缩进，不允许管理员写入任意样式类。
export const MATERIAL_FIRST_LINE_INDENT_CLASS = 'material-first-line-indent'
const ALLOWED_MATERIAL_TAGS = new Set([
  'STRONG',
  'B',
  'BR',
  'DIV',
  'P',
  'BLOCKQUOTE',
  'UL',
  'OL',
  'LI',
])
const MATERIAL_BLOCK_TAGS = new Set(['DIV', 'P', 'BLOCKQUOTE', 'UL', 'OL', 'LI'])

/**
 * 将普通文本中的特殊字符转换为安全 HTML（超文本标记语言）实体。
 *
 * 入参：value 为必填普通字符串，可以包含任意用户粘贴内容。
 * 返回值：string：可安全写入 HTML 文本节点的转义结果。
 * 异常：当前函数不主动抛出异常。
 */
function escapeMaterialHtml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

/**
 * 递归复制资料富文本节点并仅保留允许的文档结构。
 *
 * 入参：source 为待清洗节点；targetParent 为接收安全节点的父节点，均必填。
 * 返回值：void：安全节点直接追加到目标父节点。
 * 异常：当前函数不主动抛出异常；非白名单标签会移除标签但保留文字子节点。
 */
function appendSanitizedMaterialNode(source: Node, targetParent: Node): void {
  if (source.nodeType === Node.TEXT_NODE) {
    targetParent.appendChild(document.createTextNode(source.textContent ?? ''))
    return
  }
  if (source.nodeType !== Node.ELEMENT_NODE) {
    return
  }

  const sourceElement = source as HTMLElement
  if (!ALLOWED_MATERIAL_TAGS.has(sourceElement.tagName)) {
    sourceElement.childNodes.forEach((child) => appendSanitizedMaterialNode(child, targetParent))
    return
  }

  const normalizedTag = sourceElement.tagName === 'B'
    ? 'strong'
    : sourceElement.tagName.toLowerCase()
  const safeElement = document.createElement(normalizedTag)
  if (
    ['P', 'DIV'].includes(sourceElement.tagName)
    && sourceElement.classList.contains(MATERIAL_FIRST_LINE_INDENT_CLASS)
  ) {
    safeElement.classList.add(MATERIAL_FIRST_LINE_INDENT_CLASS)
  }
  sourceElement.childNodes.forEach((child) => appendSanitizedMaterialNode(child, safeElement))
  targetParent.appendChild(safeElement)
}

/**
 * 将安全富文本节点递归转换为适合摘要和空值校验的普通文本。
 *
 * 入参：source 为必填 DOM（文档对象模型）节点。
 * 返回值：string：保留块级结构换行并为列表项添加项目符号的普通文本。
 * 异常：当前函数不主动抛出异常。
 */
function materialNodeToPlainText(source: Node): string {
  if (source.nodeType === Node.TEXT_NODE) {
    return source.textContent ?? ''
  }
  if (source.nodeType !== Node.ELEMENT_NODE) {
    return ''
  }
  const sourceElement = source as HTMLElement
  if (sourceElement.tagName === 'BR') {
    return '\n'
  }
  const childText = Array.from(sourceElement.childNodes)
    .map((child) => materialNodeToPlainText(child))
    .join('')
  if (sourceElement.tagName === 'LI') {
    return `• ${childText.trim()}\n`
  }
  return MATERIAL_BLOCK_TAGS.has(sourceElement.tagName)
    ? `${childText.trimEnd()}\n`
    : childText
}

/**
 * 清洗会议资料富文本，仅保留轻量文档编辑所需的安全标签。
 *
 * 入参：value 为必填 HTML 字符串，可以为空或包含粘贴样式。
 * 返回值：string：删除脚本、属性、链接、图片和非白名单标签后的安全 HTML。
 * 异常：浏览器无法解析或当前不在浏览器环境时返回空字符串。
 * 使用示例：`<strong onclick="x()">重点</strong>` 返回 `<strong>重点</strong>`。
 */
export function sanitizeMaterialRichHtml(value: string): string {
  if (!value.trim() || typeof document === 'undefined') {
    return ''
  }
  const source = document.createElement('template')
  const target = document.createElement('div')
  source.innerHTML = value
  source.content.childNodes.forEach((child) => appendSanitizedMaterialNode(child, target))
  return target.innerHTML.trim()
}

/**
 * 将历史普通多行资料正文转换为安全文档 HTML。
 *
 * 入参：value 为必填普通文本，允许换行和缩进。
 * 返回值：string：逐行转义并使用段落元素表达换行的安全 HTML。
 * 异常：当前函数不主动抛出异常；空正文返回空字符串。
 */
export function materialPlainTextToHtml(value: string): string {
  if (!value.trim()) {
    return ''
  }
  const lines = value.replaceAll('\r\n', '\n').split('\n')
  return lines
    .map((line) => `<p>${line ? escapeMaterialHtml(line) : '<br>'}</p>`)
    .join('')
}

/**
 * 将资料内容字段解码为可供编辑器和嘉宾端展示的安全 HTML。
 *
 * 入参：value 为必填资料内容；可以是新版编码或历史普通文本。
 * 返回值：string：白名单清洗后的文档 HTML。
 * 异常：编码损坏时不抛出异常，而是按历史普通文本安全转换。
 */
export function decodeMaterialRichContent(value: string): string {
  if (!value.startsWith(MATERIAL_RICH_CONTENT_PREFIX)) {
    return materialPlainTextToHtml(value)
  }
  try {
    return sanitizeMaterialRichHtml(
      decodeURIComponent(value.slice(MATERIAL_RICH_CONTENT_PREFIX.length)),
    )
  } catch {
    return materialPlainTextToHtml(value)
  }
}

/**
 * 将资料文档 HTML 编码为可继续保存到现有正文列的字符串。
 *
 * 入参：value 为必填编辑器 HTML。
 * 返回值：string：带 `material-rich:` 前缀的 URI 编码内容；无可见文字时返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
export function encodeMaterialRichContent(value: string): string {
  const safeHtml = sanitizeMaterialRichHtml(value)
  if (!materialRichHtmlToPlainText(safeHtml)) {
    return ''
  }
  return `${MATERIAL_RICH_CONTENT_PREFIX}${encodeURIComponent(safeHtml)}`
}

/**
 * 将会议资料富文本转换为普通文本摘要。
 *
 * 入参：value 为必填安全或待清洗 HTML。
 * 返回值：string：去除多余空白并保留文档段落换行的普通文本。
 * 异常：当前函数不主动抛出异常；非浏览器环境返回空字符串。
 */
export function materialRichHtmlToPlainText(value: string): string {
  const safeHtml = sanitizeMaterialRichHtml(value)
  if (!safeHtml || typeof document === 'undefined') {
    return ''
  }
  const container = document.createElement('div')
  container.innerHTML = safeHtml
  return Array.from(container.childNodes)
    .map((child) => materialNodeToPlainText(child))
    .join('')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

/**
 * 将数据库中的资料内容直接转换为后台列表摘要。
 *
 * 入参：value 为必填资料内容，可以是新版编码或历史普通文本。
 * 返回值：string：适合两行预览的普通文本。
 * 异常：当前函数不主动抛出异常。
 */
export function meetingMaterialContentPreview(value: string): string {
  return materialRichHtmlToPlainText(decodeMaterialRichContent(value))
}
