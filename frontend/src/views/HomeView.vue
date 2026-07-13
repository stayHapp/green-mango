<template>
  <section class="page hero-grid">
    <div>
      <p class="eyebrow">三端交互校验</p>
      <h1>先用 JSON mock 数据跑通会议签到闭环</h1>
      <p class="lead">当前页面用于验证管理员端、嘉宾端、工作人员端的核心流程，不连接后端业务 API。</p>
    </div>
    <div class="workflow-panel">
      <div class="workflow-step">管理员创建会议并录入嘉宾</div>
      <div class="workflow-step">嘉宾登录后展示个人二维码</div>
      <div class="workflow-step">工作人员扫码完成签到</div>
      <div class="workflow-step">管理员查看签到情况</div>
    </div>
  </section>
</template>
