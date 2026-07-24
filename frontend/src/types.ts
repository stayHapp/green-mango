/** 前端三端页面与 API 适配层使用的共享业务类型。 */
export type ClientRole = 'admin' | 'guest' | 'staff'

export type MeetingStatus = 'draft' | 'published' | 'ended'

export interface Meeting {
  id: string
  title: string
  description: string
  location: string
  navigationName: string
  navigationAddress: string
  publicUrl?: string
  navigationLongitude?: number
  navigationLatitude?: number
  startTime: string
  endTime: string
  status: MeetingStatus
  registrationEnabled?: boolean
  registrationFields?: GuestRegistrationField[]
  adminIds: string[]
  staffIds: string[]
}

export type MeetingUpdateInput = Pick<
  Meeting,
  'title' | 'description' | 'location' | 'startTime' | 'endTime' | 'status' | 'publicUrl'
>

export type MeetingCreateInput = MeetingUpdateInput

export interface GuestRegistrationField {
  key: string
  label: string
  required: boolean
}

export interface GuestApplicationInput {
  name: string
  phone: string
  organization?: string
  title?: string
  tag?: string
  seat?: string
  values?: Record<string, string>
}

export interface GuestApplicationResult {
  id: string
  meetingId: string
  status: 'pending' | 'approved' | 'rejected'
  createdAt: string
}

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
  required: boolean
  visibleToGuest: boolean
  usedForLogin: boolean
  sortOrder: number
  isEnabled: boolean
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
  source?: 'admin_entry' | 'admin_import' | 'self_registration'
  visibleFields?: string[]
  fieldLabels?: Record<string, string>
  values?: Record<string, string | null>
}

export interface GuestImportInput {
  name: string
  phone: string
  organization?: string
  title?: string
  tag?: string
  seat?: string
  values?: Record<string, string | null>
}

export interface GuestImportResult {
  importedCount: number
  invalidRows: number[]
}

export interface GuestCheckInQr {
  qrToken: string
  expiresAt: string
  isCheckedIn: boolean
  checkedInAt: string
}

export type MeetingAssistantFeatureKey = 'agenda' | 'manual' | 'weather' | 'route' | 'contact'

export interface MeetingContactPerson {
  name: string
  role: string
  phone: string
}

export interface MeetingAssistantFeature {
  meetingId: string
  key: MeetingAssistantFeatureKey
  title: string
  description: string
  content: string
  unpublishedMessage: string
  isPublished: boolean
  contacts: MeetingContactPerson[]
}

export interface StaffUser {
  id: string
  name: string
  phone: string
  account: string
  meetingIds: string[]
  isActive?: boolean
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

export interface AdminCheckInRecord {
  guestId: string
  guestName: string
  phone: string
  checkedInAt: string
  method: 'scan' | 'manual'
  staffName: string
}

export interface AdminCheckInSummary {
  totalGuests: number
  checkedInCount: number
  uncheckedCount: number
  records: AdminCheckInRecord[]
}

export type ScanStatus = 'success' | 'already_checked_in' | 'expired' | 'invalid' | 'wrong_meeting'

export interface ScanResult {
  status: ScanStatus
  message: string
  guest?: Guest
  checkIn?: CheckInRecord
}
