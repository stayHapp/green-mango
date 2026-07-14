/**
 * 前端 mock 原型中使用的共享类型。
 *
 * 这些类型用于约束 JSON 数据和页面交互，不代表最终后端 API 已定稿。
 */
export type ClientRole = 'admin' | 'guest' | 'staff'

export type MeetingStatus = 'draft' | 'published' | 'ended'

export interface Meeting {
  id: string
  title: string
  description: string
  location: string
  startTime: string
  endTime: string
  status: MeetingStatus
  adminIds: string[]
  staffIds: string[]
}

export type MeetingUpdateInput = Pick<Meeting, 'title' | 'description' | 'location' | 'startTime' | 'endTime' | 'status'>

export type MeetingCreateInput = MeetingUpdateInput

export interface AdminUser {
  id: string
  name: string
  phone: string
}

export interface GuestField {
  id: string
  meetingId: string
  label: string
  key: string
  type: 'text' | 'phone' | 'tag' | 'seat'
  visibleToGuest: boolean
  usedForLogin: boolean
  sortOrder: number
}

export interface Guest {
  id: string
  meetingId: string
  name: string
  phone: string
  tag: string
  organization: string
  title: string
  seat: string
  qrToken: string
}

export interface GuestImportInput {
  name: string
  phone: string
  organization?: string
  title?: string
  tag?: string
  seat?: string
}

export interface GuestImportResult {
  importedCount: number
  invalidRows: number[]
}

export interface GuestQrGenerationResult {
  generatedCount: number
  existingCount: number
}

export interface StaffUser {
  id: string
  name: string
  phone: string
  account: string
  meetingIds: string[]
}

export interface StaffCreateInput {
  name: string
  phone: string
  account: string
}

export type IdentityLoginResult =
  | { role: 'admin'; user: AdminUser }
  | { role: 'guest'; user: Guest }
  | { role: 'staff'; user: StaffUser }

export interface CheckInRecord {
  id: string
  meetingId: string
  guestId: string
  staffId: string
  checkedInAt: string
  method: 'scan' | 'manual'
}

export interface MockData {
  meetings: Meeting[]
  admins: AdminUser[]
  guestFields: GuestField[]
  guests: Guest[]
  staff: StaffUser[]
  checkIns: CheckInRecord[]
}

export type ScanStatus = 'success' | 'already_checked_in' | 'expired' | 'invalid' | 'wrong_meeting'

export interface ScanResult {
  status: ScanStatus
  message: string
  guest?: Guest
  checkIn?: CheckInRecord
}
