/**
 * 前端路由配置。
 *
 * 正式入口默认进入管理员登录页；嘉宾和工作人员仍通过会议专属链接进入。
 */
import { createRouter, createWebHistory } from 'vue-router'

import LoginView from '../views/LoginView.vue'
import AdminMeetingsView from '../views/admin/AdminMeetingsView.vue'
import AdminMeetingDetailView from '../views/admin/AdminMeetingDetailView.vue'
import AdminLoginView from '../views/admin/AdminLoginView.vue'
import GuestMeetingsView from '../views/guest/GuestMeetingsView.vue'
import GuestMeetingDetailView from '../views/guest/GuestMeetingDetailView.vue'
import GuestAssistantFeatureView from '../views/guest/GuestAssistantFeatureView.vue'
import StaffMeetingsView from '../views/staff/StaffMeetingsView.vue'
import StaffCheckInView from '../views/staff/StaffCheckInView.vue'
import GuestEntryView from '../views/guest/GuestEntryView.vue'
import GuestRegisterView from '../views/guest/GuestRegisterView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', name: 'login', component: LoginView },
    { path: '/meetings/:id', name: 'meeting-entry', component: GuestEntryView },
    { path: '/meetings/:id/register', name: 'guest-register', component: GuestRegisterView },
    { path: '/meetings/:id/staff/login', name: 'meeting-staff-login', component: () => import('../views/staff/StaffLoginView.vue') },
    { path: '/admin/login', name: 'admin-login', component: AdminLoginView },
    { path: '/admin/meetings', name: 'admin-meetings', component: AdminMeetingsView },
    { path: '/admin/meetings/:id', name: 'admin-meeting-detail', component: AdminMeetingDetailView },
    { path: '/guest/login', name: 'guest-login', component: () => import('../views/guest/GuestLoginView.vue') },
    { path: '/guest/meetings', name: 'guest-meetings', component: GuestMeetingsView },
    { path: '/guest/meetings/:id', name: 'guest-meeting-detail', component: GuestMeetingDetailView },
    { path: '/guest/meetings/:id/assistant/:featureKey', name: 'guest-assistant-feature', component: GuestAssistantFeatureView },
    { path: '/staff/meetings', name: 'staff-meetings', component: StaffMeetingsView },
    { path: '/staff/meetings/:id/check-in', name: 'staff-check-in', component: StaffCheckInView },
  ],
})
