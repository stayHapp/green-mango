/** 会议资料多条目维护、读取和附件下载 API。 */

import type { MeetingMaterial } from '../types'
import { apiClient, authorizationConfig } from './client'

interface MeetingMaterialApiResponse {
  id: number
  meeting_id: number
  title: string
  content: string
  original_filename: string | null
  content_type: string | null
  size_bytes: number | null
  sort_order: number
  created_at: string
  updated_at: string
}

export interface MeetingMaterialInput {
  title: string
  content: string
  attachment?: File
  removeAttachment?: boolean
}

export type MeetingMaterialAccess = 'admin' | 'guest' | 'public'

/**
 * 将后端会议资料响应转换为前端页面类型。
 *
 * 入参：response 为后端单条会议资料响应，必填。
 * 返回值：MeetingMaterial：字段名称已转换且空附件字段已规范化的资料对象。
 * 异常：当前函数不主动抛出异常。
 */
function mapMeetingMaterial(response: MeetingMaterialApiResponse): MeetingMaterial {
  return {
    id: String(response.id),
    meetingId: String(response.meeting_id),
    title: response.title,
    content: response.content,
    originalFilename: response.original_filename ?? '',
    contentType: response.content_type ?? '',
    sizeBytes: response.size_bytes ?? undefined,
    sortOrder: response.sort_order,
    createdAt: response.created_at,
    updatedAt: response.updated_at,
  }
}

/**
 * 将资料编辑值转换为后端 multipart/form-data（多部分表单）请求。
 *
 * 入参：input 为标题、正文、可选附件和删除附件标记，必填。
 * 返回值：FormData：可以直接提交给新增或编辑接口的表单对象。
 * 异常：当前函数不主动抛出异常。
 */
function buildMaterialFormData(input: MeetingMaterialInput): FormData {
  const formData = new FormData()
  formData.append('title', input.title)
  formData.append('content', input.content)
  formData.append('remove_attachment', String(Boolean(input.removeAttachment)))
  if (input.attachment) {
    formData.append('attachment', input.attachment)
  }
  return formData
}

/**
 * 获取管理员有权维护会议的全部资料。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<MeetingMaterial[]>：按后台排序返回的资料列表。
 * 异常：登录失效、会议无权限或网络失败时抛出异常。
 */
export async function listAdminMeetingMaterials(meetingId: string): Promise<MeetingMaterial[]> {
  const { data } = await apiClient.get<MeetingMaterialApiResponse[]>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/materials`,
    authorizationConfig('admin'),
  )
  return data.map(mapMeetingMaterial)
}

/**
 * 新增一条会议资料。
 *
 * 入参：meetingId 为会议 ID；input 为资料标题、正文和可选附件，均必填。
 * 返回值：Promise<MeetingMaterial>：保存后的资料对象。
 * 异常：表单、附件、权限或网络异常时抛出异常。
 */
export async function createAdminMeetingMaterial(
  meetingId: string,
  input: MeetingMaterialInput,
): Promise<MeetingMaterial> {
  const { data } = await apiClient.post<MeetingMaterialApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/materials`,
    buildMaterialFormData(input),
    authorizationConfig('admin', { headers: { 'Content-Type': 'multipart/form-data' } }),
  )
  return mapMeetingMaterial(data)
}

/**
 * 编辑一条会议资料并按需替换或移除附件。
 *
 * 入参：meetingId 为会议 ID；materialId 为资料 ID；input 为完整编辑值，均必填。
 * 返回值：Promise<MeetingMaterial>：保存后的资料对象。
 * 异常：资料不存在、表单、附件、权限或网络异常时抛出异常。
 */
export async function updateAdminMeetingMaterial(
  meetingId: string,
  materialId: string,
  input: MeetingMaterialInput,
): Promise<MeetingMaterial> {
  const { data } = await apiClient.patch<MeetingMaterialApiResponse>(
    `/admin/meetings/${encodeURIComponent(meetingId)}/materials/${encodeURIComponent(materialId)}`,
    buildMaterialFormData(input),
    authorizationConfig('admin', { headers: { 'Content-Type': 'multipart/form-data' } }),
  )
  return mapMeetingMaterial(data)
}

/**
 * 删除一条会议资料及其附件。
 *
 * 入参：meetingId 为会议 ID；materialId 为资料 ID，均必填。
 * 返回值：Promise<void>：后端确认删除后结束。
 * 异常：资料不存在、权限或网络异常时抛出异常。
 */
export async function deleteAdminMeetingMaterial(meetingId: string, materialId: string): Promise<void> {
  await apiClient.delete(
    `/admin/meetings/${encodeURIComponent(meetingId)}/materials/${encodeURIComponent(materialId)}`,
    authorizationConfig('admin'),
  )
}

/**
 * 获取已登录嘉宾所属会议的已发布资料。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<MeetingMaterial[]>：已发布资料列表。
 * 异常：嘉宾未登录、跨会议访问、资料未发布或网络失败时抛出异常。
 */
export async function listGuestMeetingMaterials(meetingId: string): Promise<MeetingMaterial[]> {
  const { data } = await apiClient.get<MeetingMaterialApiResponse[]>(
    `/guest/meetings/${encodeURIComponent(meetingId)}/materials`,
    authorizationConfig('guest'),
  )
  return data.map(mapMeetingMaterial)
}

/**
 * 获取无需登录即可查看的公开会议资料。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<MeetingMaterial[]>：公开且已发布的资料列表。
 * 异常：会议不可公开、资料仅限嘉宾、未发布或网络失败时抛出异常。
 */
export async function listPublicMeetingMaterials(meetingId: string): Promise<MeetingMaterial[]> {
  const { data } = await apiClient.get<MeetingMaterialApiResponse[]>(
    `/meetings/${encodeURIComponent(meetingId)}/materials`,
  )
  return data.map(mapMeetingMaterial)
}

/**
 * 下载指定访问模式下的会议资料附件。
 *
 * 入参：meetingId 为会议 ID；materialId 为资料 ID；access 为管理员、嘉宾或公开模式。
 * 返回值：Promise<Blob>：后端返回的附件二进制对象。
 * 异常：权限不足、附件不存在、登录失效或网络失败时抛出异常。
 */
export async function downloadMeetingMaterialAttachment(
  meetingId: string,
  materialId: string,
  access: MeetingMaterialAccess,
): Promise<Blob> {
  const prefix = access === 'admin' ? '/admin/meetings' : access === 'guest' ? '/guest/meetings' : '/meetings'
  const path = `${prefix}/${encodeURIComponent(meetingId)}/materials/${encodeURIComponent(materialId)}/download`
  const config = access === 'public'
    ? { responseType: 'blob' as const }
    : authorizationConfig(access, { responseType: 'blob' })
  const response = await apiClient.get<Blob>(path, config)
  return response.data
}

/**
 * 触发浏览器保存后端返回的会议资料附件。
 *
 * 入参：content 为附件 Blob（二进制对象）；filename 为管理员上传时的原始文件名，均必填。
 * 返回值：void：临时生成下载链接并在触发后释放对象地址。
 * 异常：浏览器不支持对象地址或禁止程序化下载时抛出异常。
 */
export function saveMeetingMaterialBlob(content: Blob, filename: string): void {
  const objectUrl = URL.createObjectURL(content)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = filename
  link.click()
  URL.revokeObjectURL(objectUrl)
}
