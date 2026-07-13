/**
 * 前端路由配置。
 *
 * 当前原型按管理员端、嘉宾端、工作人员端组织页面，用于验证三端交互路径。
 */
import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import AdminMeetingsView from '../views/admin/AdminMeetingsView.vue'
import AdminMeetingDetailView from '../views/admin/AdminMeetingDetailView.vue'
import GuestMeetingsView from '../views/guest/GuestMeetingsView.vue'
import GuestMeetingDetailView from '../views/guest/GuestMeetingDetailView.vue'
import StaffMeetingsView from '../views/staff/StaffMeetingsView.vue'
import StaffCheckInView from '../views/staff/StaffCheckInView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/login', name: 'login', component: LoginView },
    { path: '/admin/login', redirect: (to) => ({ path: '/login', query: to.query }) },
    { path: '/admin/meetings', name: 'admin-meetings', component: AdminMeetingsView },
    { path: '/admin/meetings/:id', name: 'admin-meeting-detail', component: AdminMeetingDetailView },
    { path: '/guest/login', redirect: (to) => ({ path: '/login', query: to.query }) },
    { path: '/guest/meetings', name: 'guest-meetings', component: GuestMeetingsView },
    { path: '/guest/meetings/:id', name: 'guest-meeting-detail', component: GuestMeetingDetailView },
    { path: '/staff/login', redirect: (to) => ({ path: '/login', query: to.query }) },
    { path: '/staff/meetings', name: 'staff-meetings', component: StaffMeetingsView },
    { path: '/staff/meetings/:id/check-in', name: 'staff-check-in', component: StaffCheckInView },
  ],
})
