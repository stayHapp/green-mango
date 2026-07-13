<template>
  <el-container class="app-shell">
    <el-header class="topbar">
      <router-link class="brand" to="/">
        <span class="brand-name">知会</span>
        <span class="brand-subtitle">会议与签到原型</span>
      </router-link>
      <nav class="topnav">
        <router-link to="/login?meetingId=m-edu-2026">统一登录</router-link>
      </nav>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>
