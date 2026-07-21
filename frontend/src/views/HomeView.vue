<template>
  <section class="page hero-grid">
    <div>
      <p class="eyebrow">关于「知会」</p>
      <h1>面向教育会议的嘉宾与签到管理平台</h1>
      <p class="lead">
        知会帮助活动组织者创建会议、录入嘉宾、维护会议服务，并在现场完成嘉宾签到。
        管理员、工作人员和嘉宾通过各自的入口进入系统。
      </p>
    </div>
    <div class="workflow-panel">
      <div class="workflow-step">管理员通过管理后台创建会议并录入嘉宾</div>
      <div class="workflow-step">嘉宾使用会议专属二维码查看会议信息与签到凭证</div>
      <div class="workflow-step">工作人员通过会议专属入口扫码完成现场签到</div>
      <div class="workflow-step">管理员在管理后台查看签到情况并导出签到表</div>
    </div>
    <div class="home-note">
      <p class="muted">
        嘉宾和工作人员请通过会议专属二维码或链接进入；管理员请直接访问
        <router-link to="/login">管理后台</router-link>。
      </p>
    </div>
  </section>
</template>
