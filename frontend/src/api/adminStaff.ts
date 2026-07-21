/** 管理员工作人员查询、创建、修改和会议授权维护 API。 */

import type { StaffUser } from '../types'
import { apiClient, authorizationConfig } from './client'

interface StaffResponse {
  id: number
  username: string
  is_active: boolean
}

export interface AdminStaffCreateInput {
  username: string
  initialPassword: string
}

export interface AdminStaffUpdateInput {
  isActive?: boolean
  newPassword?: string
}

/**
 * 将后端工作人员响应转换为前端共享结构。
 *
 * 入参：staff 为后端工作人员响应，必填；meetingId 为当前授权会议 ID，必填。
 * 返回值：StaffUser：仅包含账号、授权和启用状态的工作人员。
 * 异常：当前函数不主动抛出异常。
 */
function mapStaff(staff: StaffResponse, meetingId: string): StaffUser {
  return {
    id: String(staff.id),
    name: staff.username,
    phone: '',
    account: staff.username,
    meetingIds: [meetingId],
    isActive: staff.is_active,
  }
}

/**
 * 查询当前会议已授权的工作人员。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<StaffUser[]>：按后端顺序返回工作人员列表。
 * 异常：登录失效、会议无权限或网络失败时抛出 Axios 异常。
 */
export async function listAdminStaff(meetingId: string): Promise<StaffUser[]> {
  const { data } = await apiClient.get<StaffResponse[]>(
    `/admin/meetings/${meetingId}/staff`,
    authorizationConfig('admin'),
  )
  return data.map((staff) => mapStaff(staff, meetingId))
}

/**
 * 创建工作人员账号或复用同名工作人员，并授权当前会议。
 *
 * 入参：meetingId 为会议 ID；input 为账号和初始密码，均必填。
 * 返回值：Promise<StaffUser>：已创建或已授权的工作人员。
 * 异常：字段校验、账号角色冲突、权限或网络异常时抛出 Axios 异常。
 */
export async function createAdminStaff(meetingId: string, input: AdminStaffCreateInput): Promise<StaffUser> {
  const { data } = await apiClient.post<StaffResponse>(
    `/admin/meetings/${meetingId}/staff`,
    {
      username: input.username,
      initial_password: input.initialPassword,
    },
    authorizationConfig('admin'),
  )
  return mapStaff(data, meetingId)
}

/**
 * 修改工作人员启用状态或登录密码。
 *
 * 入参：meetingId、staffId 为资源 ID；input 为需要修改的字段，均必填。
 * 返回值：Promise<StaffUser>：修改后的工作人员。
 * 异常：字段校验、资源不存在、权限或网络异常时抛出 Axios 异常。
 */
export async function updateAdminStaff(
  meetingId: string,
  staffId: string,
  input: AdminStaffUpdateInput,
): Promise<StaffUser> {
  const payload: Record<string, string | boolean> = {}
  if (input.isActive !== undefined) payload.is_active = input.isActive
  if (input.newPassword) payload.new_password = input.newPassword
  const { data } = await apiClient.patch<StaffResponse>(
    `/admin/meetings/${meetingId}/staff/${staffId}`,
    payload,
    authorizationConfig('admin'),
  )
  return mapStaff(data, meetingId)
}

/**
 * 解除工作人员对当前会议的授权，不删除账号及其他会议授权。
 *
 * 入参：meetingId、staffId 分别为会议和工作人员 ID，均必填。
 * 返回值：Promise<void>：后端确认解除授权后结束。
 * 异常：授权不存在、权限或网络异常时抛出 Axios 异常。
 */
export async function removeAdminStaffAssignment(meetingId: string, staffId: string): Promise<void> {
  await apiClient.delete(
    `/admin/meetings/${meetingId}/staff/${staffId}`,
    authorizationConfig('admin'),
  )
}
