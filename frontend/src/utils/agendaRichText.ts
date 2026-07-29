const RICH_CONTENT_PREFIX = 'rich:'
const ALLOWED_AGENDA_TAGS = new Set(['STRONG', 'B', 'BR', 'DIV', 'P', 'BLOCKQUOTE'])

/**
 * 将普通文本中的特殊字符转换为安全的 HTML 实体。
 *
 * 入参：value 为必填字符串，可以包含任意普通文本。
 * 返回值：string：可安全放入 HTML 文本节点的转义结果。
 * 异常：当前函数不主动抛出异常。
 */
function escapeAgendaHtml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

/**
 * 递归复制富文本节点，并只保留会议日程允许的标签。
 *
 * 入参：
 * - source：必填，待清洗的原始 DOM 节点。
 * - targetParent：必填，接收安全节点的目标 DOM 节点。
 * 返回值：void；函数直接向目标节点追加白名单内容。
 * 异常：当前函数不主动抛出异常；不支持的元素会被移除标签但保留其文字子节点。
 */
function appendSanitizedAgendaNode(source: Node, targetParent: Node): void {
  if (source.nodeType === Node.TEXT_NODE) {
    targetParent.appendChild(document.createTextNode(source.textContent ?? ''))
    return
  }
  if (source.nodeType !== Node.ELEMENT_NODE) {
    return
  }

  const sourceElement = source as HTMLElement
  if (!ALLOWED_AGENDA_TAGS.has(sourceElement.tagName)) {
    sourceElement.childNodes.forEach((child) => appendSanitizedAgendaNode(child, targetParent))
    return
  }

  const normalizedTag = sourceElement.tagName === 'B'
    ? 'strong'
    : sourceElement.tagName.toLowerCase()
  const safeElement = document.createElement(normalizedTag)
  sourceElement.childNodes.forEach((child) => appendSanitizedAgendaNode(child, safeElement))
  targetParent.appendChild(safeElement)
}

/**
 * 清洗会议日程富文本，仅保留加粗、换行、段落和缩进结构。
 *
 * 入参：value 为必填 HTML 字符串，可以为空。
 * 返回值：string：删除脚本、属性和非白名单标签后的安全 HTML。
 * 异常：当前函数不主动抛出异常；浏览器无法解析时返回空字符串。
 * 使用示例：`<strong onclick="x()">重点</strong>` 返回 `<strong>重点</strong>`。
 */
export function sanitizeAgendaRichHtml(value: string): string {
  if (!value.trim() || typeof document === 'undefined') {
    return ''
  }
  const source = document.createElement('template')
  const target = document.createElement('div')
  source.innerHTML = value
  source.content.childNodes.forEach((child) => appendSanitizedAgendaNode(child, target))
  return target.innerHTML.trim()
}

/**
 * 将普通多行文本转换为日程富文本 HTML。
 *
 * 入参：value 为必填普通文本，允许包含换行和全角空格缩进。
 * 返回值：string：逐行转义并使用 `div`、`br` 表达换行的安全 HTML。
 * 异常：当前函数不主动抛出异常。
 */
export function agendaPlainTextToHtml(value: string): string {
  if (!value.trim()) {
    return ''
  }
  const lines = value.replaceAll('\r\n', '\n').split('\n')
  return lines
    .map((line) => `<div>${line ? escapeAgendaHtml(line) : '<br>'}</div>`)
    .join('')
}

/**
 * 将清洗后的富文本编码为可安全放入单行日程正文的字段。
 *
 * 入参：value 为必填 HTML 字符串。
 * 返回值：string：带 `rich:` 前缀的 URI 编码字段；空内容返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
export function encodeAgendaRichContent(value: string): string {
  const safeHtml = sanitizeAgendaRichHtml(value)
  return safeHtml ? `${RICH_CONTENT_PREFIX}${encodeURIComponent(safeHtml)}` : ''
}

/**
 * 将日程正文中的内容字段还原为安全富文本。
 *
 * 入参：value 为必填字段；可以是新版 `rich:` 编码或历史普通文本。
 * 返回值：string：可供受控 `v-html` 展示的白名单 HTML。
 * 异常：编码损坏时不抛出异常，而是按普通文本安全展示原值。
 */
export function decodeAgendaRichContent(value: string): string {
  if (!value.startsWith(RICH_CONTENT_PREFIX)) {
    return agendaPlainTextToHtml(value)
  }
  try {
    return sanitizeAgendaRichHtml(decodeURIComponent(value.slice(RICH_CONTENT_PREFIX.length)))
  } catch {
    return agendaPlainTextToHtml(value)
  }
}

/**
 * 判断日程内容字段是否使用新版富文本编码。
 *
 * 入参：value 为必填字段字符串。
 * 返回值：boolean：以 `rich:` 开头时返回 true，否则返回 false。
 * 异常：当前函数不主动抛出异常。
 */
export function isEncodedAgendaRichContent(value: string): boolean {
  return value.startsWith(RICH_CONTENT_PREFIX)
}
