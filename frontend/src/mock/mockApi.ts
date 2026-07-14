/**
 * 基于 JSON 数据的前端 mock API。
 *
 * 当前阶段用于校验三端交互流程，不依赖真实后端业务接口。函数签名尽量贴近未来 API，后续替换为 Axios 请求时可以降低页面改动成本。
 */
import rawData from './data.json'
import type {
  AdminUser,
  CheckInRecord,
  Guest,
  GuestImportInput,
  GuestImportResult,
  GuestQrGenerationResult,
  IdentityLoginResult,
  Meeting,
  MeetingCreateInput,
  MeetingUpdateInput,
  MockData,
  ScanResult,
  StaffCreateInput,
  StaffUser,
} from '../types'

const data = rawData as MockData
let checkIns: CheckInRecord[] = [...data.checkIns]

/**
 * 模拟异步请求延迟。
 *
 * 入参：
 *   value：需要返回的数据，必填。
 *
 * 返回值：
 *   Promise<T>：延迟返回的 mock 数据。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => window.setTimeout(() => resolve(value), 120))
}

/**
 * 获取全部会议。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   Promise<Meeting[]>：会议列表。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常。
 */
export function listMeetings(): Promise<Meeting[]> {
  return delay(data.meetings)
}

/**
 * 获取指定管理员可管理的会议。
 *
 * 入参：
 *   adminId：管理员 ID，必填。
 *
 * 返回值：
 *   Promise<Meeting[]>：该管理员拥有管理权限的会议列表。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常。
 */
export function listAdminMeetings(adminId: string): Promise<Meeting[]> {
  return delay(data.meetings.filter((meeting) => meeting.adminIds.includes(adminId)))
}

/**
 * 获取指定会议详情。
 *
 * 入参：
 *   meetingId：会议 ID，必填。
 *
 * 返回值：
 *   Promise<Meeting | undefined>：匹配会议；不存在时返回 undefined。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常。
 */
export function getMeeting(meetingId: string): Promise<Meeting | undefined> {
  return delay(data.meetings.find((meeting) => meeting.id === meetingId))
}

/**
 * 更新指定会议的基础信息。
 *
 * 入参：
 *   meetingId：会议 ID，必填。
 *   input：会议更新数据，必填，包含标题、说明、地点、起止时间和状态。
 *
 * 返回值：
 *   Promise<Meeting | undefined>：更新后的会议；会议不存在时返回 undefined。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常；真实 API 应补充权限和字段校验。
 */
export function updateMeeting(meetingId: string, input: MeetingUpdateInput): Promise<Meeting | undefined> {
  const meeting = data.meetings.find((item) => item.id === meetingId)

  if (!meeting) {
    return delay(undefined)
  }

  Object.assign(meeting, input)
  return delay(meeting)
}

/**
 * 创建会议并将当前管理员设为会议管理员。
 *
 * 入参：adminId 为管理员 ID；input 为必填的会议基础信息。
 * 返回值：Promise<Meeting>：新建的会议。
 * 异常：当前 mock 不主动抛出异常；真实 API 应校验管理员身份与时间字段。
 */
export function createMeeting(adminId: string, input: MeetingCreateInput): Promise<Meeting> {
  const meeting: Meeting = { id: `m-${Date.now()}`, ...input, adminIds: [adminId], staffIds: [] }
  data.meetings.push(meeting)
  return delay(meeting)
}

/**
 * 获取指定会议的嘉宾字段配置。
 *
 * 入参：
 *   meetingId：会议 ID，必填。
 *
 * 返回值：
 *   Promise：按排序返回的嘉宾字段配置。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常。
 */
export function listGuestFields(meetingId: string) {
  return delay(
    data.guestFields
      .filter((field) => field.meetingId === meetingId)
      .sort((left, right) => left.sortOrder - right.sortOrder),
  )
}

/**
 * 获取指定会议的嘉宾列表。
 *
 * 入参：
 *   meetingId：会议 ID，必填。
 *
 * 返回值：
 *   Promise<Guest[]>：属于该会议的嘉宾列表。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常。
 */
export function listGuests(meetingId: string): Promise<Guest[]> {
  return delay(data.guests.filter((guest) => guest.meetingId === meetingId))
}

/**
 * 将已校验的嘉宾名单写入指定会议的 mock 数据。
 *
 * 入参：
 *   meetingId：会议 ID，必填。
 *   rows：待导入嘉宾行，必填；姓名和手机号为空的行会被拒绝。
 *
 * 返回值：
 *   Promise<GuestImportResult>：返回成功导入数量和按 Excel 行号标记的无效行。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常；真实 API 还应校验管理员权限与手机号重复情况。
 */
export function importGuests(meetingId: string, rows: GuestImportInput[]): Promise<GuestImportResult> {
  const invalidRows: number[] = []
  let importedCount = 0

  // 逐行校验固定登录所需的姓名和手机号，仅将合格数据加入当前会议。
  for (const [index, row] of rows.entries()) {
    if (!row.name.trim() || !row.phone.trim()) {
      invalidRows.push(index + 2)
      continue
    }

    const suffix = `${Date.now()}-${index}`
    data.guests.push({
      id: `g-import-${suffix}`,
      meetingId,
      name: row.name.trim(),
      phone: row.phone.trim(),
      organization: row.organization?.trim() ?? '',
      title: row.title?.trim() ?? '',
      tag: row.tag?.trim() ?? '参会嘉宾',
      seat: row.seat?.trim() ?? '',
      qrToken: `QR-IMPORT-${suffix}`,
    })
    importedCount += 1
  }

  return delay({ importedCount, invalidRows })
}

/**
 * 为会议嘉宾补齐个人二维码凭证，不覆盖已有凭证。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<GuestQrGenerationResult>：返回新生成与已存在的二维码数量。
 * 异常：当前 mock 不主动抛出异常；真实 API 应校验会议管理员权限。
 */
export function generateGuestQrTokens(meetingId: string): Promise<GuestQrGenerationResult> {
  let generatedCount = 0
  let existingCount = 0
  for (const [index, guest] of data.guests.filter((item) => item.meetingId === meetingId).entries()) {
    if (guest.qrToken) {
      existingCount += 1
      continue
    }
    guest.qrToken = `QR-${meetingId}-${Date.now()}-${index}`
    generatedCount += 1
  }
  return delay({ generatedCount, existingCount })
}

/**
 * 获取指定会议的工作人员列表。
 *
 * 入参：
 *   meetingId：会议 ID，必填。
 *
 * 返回值：
 *   Promise<StaffUser[]>：被授权负责该会议的工作人员列表。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常。
 */
export function listStaff(meetingId: string): Promise<StaffUser[]> {
  return delay(data.staff.filter((staff) => staff.meetingIds.includes(meetingId)))
}

/**
 * 创建工作人员账号并授权其负责指定会议。
 *
 * 入参：meetingId 为会议 ID，input 包含必填的姓名、手机号和账号。
 * 返回值：Promise<StaffUser | undefined>，账号重复或会议不存在时返回 undefined。
 * 异常：当前 mock 不主动抛出异常；真实 API 应校验会议管理员权限。
 */
export function createStaff(meetingId: string, input: StaffCreateInput): Promise<StaffUser | undefined> {
  if (!data.meetings.some((meeting) => meeting.id === meetingId) || data.staff.some((staff) => staff.account === input.account)) {
    return delay(undefined)
  }

  const staff: StaffUser = { id: `s-${Date.now()}`, name: input.name, phone: input.phone, account: input.account, meetingIds: [meetingId] }
  data.staff.push(staff)
  return delay(staff)
}

/**
 * 获取指定会议的签到记录。
 *
 * 入参：
 *   meetingId：会议 ID，必填。
 *
 * 返回值：
 *   Promise<CheckInRecord[]>：该会议的签到记录。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常。
 */
export function listCheckIns(meetingId: string): Promise<CheckInRecord[]> {
  return delay(checkIns.filter((record) => record.meetingId === meetingId))
}

/**
 * 根据姓名和手机号模拟管理员登录。
 *
 * 入参：
 *   name：管理员姓名，必填。
 *   phone：管理员手机号，必填。
 *
 * 返回值：
 *   Promise<AdminUser | undefined>：匹配到的管理员；未匹配时返回 undefined。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常。
 */
export function loginAdmin(name: string, phone: string): Promise<AdminUser | undefined> {
  return delay(data.admins.find((admin) => admin.name === name && admin.phone === phone))
}

/**
 * 根据姓名和手机号模拟嘉宾登录。
 *
 * 入参：
 *   name：嘉宾姓名，必填。
 *   phone：嘉宾手机号，必填。
 *
 * 返回值：
 *   Promise<Guest | undefined>：匹配到的嘉宾；未匹配时返回 undefined。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常。
 */
export function loginGuest(name: string, phone: string): Promise<Guest | undefined> {
  return delay(data.guests.find((guest) => guest.name === name && guest.phone === phone))
}

/**
 * 根据姓名和手机号统一识别登录身份。
 *
 * 入参：
 *   name：登录姓名，必填。
 *   phone：登录手机号，必填。
 *
 * 返回值：
 *   Promise<IdentityLoginResult | undefined>：匹配成功时返回身份类型和用户对象；未匹配时返回 undefined。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常；真实 API 应处理重名重号、身份冲突和权限校验。
 */
export function loginByIdentity(name: string, phone: string): Promise<IdentityLoginResult | undefined> {
  const admin = data.admins.find((item) => item.name === name && item.phone === phone)

  if (admin) {
    return delay({ role: 'admin', user: admin })
  }

  const staff = data.staff.find((item) => item.name === name && item.phone === phone)

  if (staff) {
    return delay({ role: 'staff', user: staff })
  }

  const guest = data.guests.find((item) => item.name === name && item.phone === phone)

  if (guest) {
    return delay({ role: 'guest', user: guest })
  }

  return delay(undefined)
}

/**
 * 根据账号模拟工作人员登录。
 *
 * 入参：
 *   account：工作人员账号，必填。
 *
 * 返回值：
 *   Promise<StaffUser | undefined>：匹配到的工作人员；未匹配时返回 undefined。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常。
 */
export function loginStaff(account: string): Promise<StaffUser | undefined> {
  return delay(data.staff.find((staff) => staff.account === account))
}

/**
 * 获取嘉宾可参加的会议。
 *
 * 入参：
 *   guestId：嘉宾 ID，必填。
 *
 * 返回值：
 *   Promise<Meeting[]>：当前 mock 中通常为一个会议，后续可扩展多会议。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常。
 */
export function listGuestMeetings(guestId: string): Promise<Meeting[]> {
  const meetingIds = data.guests.filter((guest) => guest.id === guestId).map((guest) => guest.meetingId)
  return delay(data.meetings.filter((meeting) => meetingIds.includes(meeting.id)))
}

/**
 * 获取工作人员负责的会议。
 *
 * 入参：
 *   staffId：工作人员 ID，必填。
 *
 * 返回值：
 *   Promise<Meeting[]>：工作人员被授权负责的会议列表。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常。
 */
export function listStaffMeetings(staffId: string): Promise<Meeting[]> {
  const staff = data.staff.find((item) => item.id === staffId)
  return delay(data.meetings.filter((meeting) => staff?.meetingIds.includes(meeting.id)))
}

/**
 * 模拟扫码签到。
 *
 * 入参：
 *   meetingId：会议 ID，必填。
 *   staffId：工作人员 ID，必填。
 *   qrToken：嘉宾二维码 token，必填。
 *
 * 返回值：
 *   Promise<ScanResult>：扫码结果，包含成功、重复、过期、无效或会议不匹配等状态。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常。
 */
export function scanGuest(meetingId: string, staffId: string, qrToken: string): Promise<ScanResult> {
  const meeting = data.meetings.find((item) => item.id === meetingId)
  const guest = data.guests.find((item) => item.qrToken === qrToken)

  if (!meeting || !guest) {
    return delay({ status: 'invalid', message: '二维码无效，未找到对应嘉宾。' })
  }

  if (guest.meetingId !== meetingId) {
    return delay({ status: 'wrong_meeting', message: '该二维码不属于当前会议。', guest })
  }

  if (new Date(meeting.endTime).getTime() < Date.now()) {
    return delay({ status: 'expired', message: '二维码已超过会议结束时间，不能签到。', guest })
  }

  const existed = checkIns.find((record) => record.meetingId === meetingId && record.guestId === guest.id)
  if (existed) {
    return delay({ status: 'already_checked_in', message: '该嘉宾已签到，不能重复签到。', guest, checkIn: existed })
  }

  const checkIn: CheckInRecord = {
    id: `ci-${Date.now()}`,
    meetingId,
    guestId: guest.id,
    staffId,
    checkedInAt: new Date().toISOString(),
    method: 'scan',
  }
  checkIns = [checkIn, ...checkIns]
  return delay({ status: 'success', message: '签到成功。', guest, checkIn })
}


/**
 * 手动标记嘉宾签到。
 *
 * 入参：
 *   meetingId：会议 ID，必填。
 *   staffId：工作人员 ID，必填。
 *   guestId：嘉宾 ID，必填。
 *
 * 返回值：
 *   Promise<ScanResult>：手动签到结果，成功时包含嘉宾和签到记录。
 *
 * 异常：
 *   当前 mock 实现不主动抛出异常；真实 API 应校验工作人员会议权限。
 */
export function markGuestCheckedIn(meetingId: string, staffId: string, guestId: string): Promise<ScanResult> {
  const meeting = data.meetings.find((item) => item.id === meetingId)
  const guest = data.guests.find((item) => item.id === guestId)

  if (!meeting || !guest) {
    return delay({ status: 'invalid', message: '未找到会议或嘉宾。' })
  }

  if (guest.meetingId !== meetingId) {
    return delay({ status: 'wrong_meeting', message: '该嘉宾不属于当前会议。', guest })
  }

  const existed = checkIns.find((record) => record.meetingId === meetingId && record.guestId === guest.id)
  if (existed) {
    return delay({ status: 'already_checked_in', message: '该嘉宾已签到，不能重复签到。', guest, checkIn: existed })
  }

  const checkIn: CheckInRecord = {
    id: `ci-${Date.now()}`,
    meetingId,
    guestId: guest.id,
    staffId,
    checkedInAt: new Date().toISOString(),
    method: 'manual',
  }
  checkIns = [checkIn, ...checkIns]
  return delay({ status: 'success', message: '已手动标记签到。', guest, checkIn })
}
