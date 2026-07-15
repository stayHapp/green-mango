/** 管理员 Excel 模板、嘉宾导入和签到表导出 API。 */

import { apiClient, authorizationConfig } from './client'

interface GuestImportResponse {
  imported_count: number
  errors: Array<{
    row_number: number
    message: string
  }>
}

export interface GuestImportError {
  rowNumber: number
  message: string
}

export interface GuestImportSummary {
  importedCount: number
  errors: GuestImportError[]
}

/**
 * 触发浏览器下载后端返回的二进制文件。
 *
 * 入参：content 为文件 Blob（二进制大对象），必填；filename 为下载文件名，必填。
 * 返回值：void：创建临时链接、触发下载并立即释放对象地址。
 * 异常：浏览器不支持对象地址或禁止程序化下载时由浏览器抛出异常。
 * 使用示例：`saveBlob(new Blob(['示例']), '示例.xlsx')`。
 */
function saveBlob(content: Blob, filename: string): void {
  const objectUrl = URL.createObjectURL(content)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  link.click()
  URL.revokeObjectURL(objectUrl)
}

/**
 * 下载当前会议包含动态字段的嘉宾导入模板。
 *
 * 入参：meetingId 为会议 ID，必填；meetingTitle 为会议标题，必填，用于生成本地文件名。
 * 返回值：Promise<void>：后端文件响应保存完成后结束。
 * 异常：登录失效、无会议权限或网络失败时抛出 Axios 异常。
 */
export async function downloadAdminGuestImportTemplate(meetingId: string, meetingTitle: string): Promise<void> {
  const response = await apiClient.get<Blob>(
    `/admin/meetings/${meetingId}/guests/import-template`,
    authorizationConfig('admin', { responseType: 'blob' }),
  )
  saveBlob(response.data, `${meetingTitle}-嘉宾导入模板.xlsx`)
}

/**
 * 上传当前会议的 XLSX 嘉宾名单并返回逐行导入结果。
 *
 * 入参：meetingId 为会议 ID，必填；file 为不超过 10MB 的 `.xlsx` 文件，必填。
 * 返回值：Promise<GuestImportSummary>：成功导入数量和错误行号、原因。
 * 异常：文件格式、表头、字段值、权限或网络异常时抛出 Axios 异常。
 */
export async function importAdminGuests(meetingId: string, file: File): Promise<GuestImportSummary> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await apiClient.post<GuestImportResponse>(
    `/admin/meetings/${meetingId}/guests/import`,
    formData,
    authorizationConfig('admin', { headers: { 'Content-Type': 'multipart/form-data' } }),
  )
  return {
    importedCount: response.data.imported_count,
    errors: response.data.errors.map((error) => ({ rowNumber: error.row_number, message: error.message })),
  }
}

/**
 * 下载当前会议包含已签到和未签到嘉宾的签到明细。
 *
 * 入参：meetingId 为会议 ID，必填；meetingTitle 为会议标题，必填，用于生成本地文件名。
 * 返回值：Promise<void>：后端文件响应保存完成后结束。
 * 异常：登录失效、无会议权限或网络失败时抛出 Axios 异常。
 */
export async function downloadAdminCheckInExport(meetingId: string, meetingTitle: string): Promise<void> {
  const response = await apiClient.get<Blob>(
    `/admin/meetings/${meetingId}/check-ins/export`,
    authorizationConfig('admin', { responseType: 'blob' }),
  )
  saveBlob(response.data, `${meetingTitle}-签到明细.xlsx`)
}
