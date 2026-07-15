<template>
  <section class="page hero-grid">
    <div>
      <p class="eyebrow">三端交互校验</p>
      <h1>逐步打通三端会议签到闭环</h1>
      <p class="lead">三端登录与退出已连接真实后端 API，会议、嘉宾和签到业务页面正在分阶段联调。</p>
    </div>
    <div class="workflow-panel">
      <div class="workflow-step">管理员创建会议并录入嘉宾</div>
      <div class="workflow-step">嘉宾登录后展示个人二维码</div>
      <div class="workflow-step">工作人员扫码完成签到</div>
      <div class="workflow-step">管理员查看签到情况</div>
    </div>
    <div class="portal-entry-grid">
      <router-link class="portal-entry-card" to="/login"><strong>管理与签到入口</strong><span>管理员、工作人员登录</span></router-link>
      <router-link class="portal-entry-card" to="/guest/login"><strong>嘉宾入口</strong><span>请通过会议专属二维码进入</span></router-link>
    </div>
  </section>
</template>
