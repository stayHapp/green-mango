<template>
  <AdminWorkspaceLayout
    v-if="meeting"
    :meeting-id="meeting.id"
    :meeting-title="meeting.title"
    :meeting-status="statusText(meeting.status)"
    :active-section="activeSection"
    @navigate="handleWorkspaceNavigation"
  >
    <section class="admin-detail-page">
      <div class="admin-page-heading">
      <div>
          <h1>{{ activeSectionTitle }}</h1>
          <p class="muted">{{ meeting.location }}｜{{ formatDate(meeting.startTime) }} - {{ formatDate(meeting.endTime) }}</p>
      </div>
      <div class="heading-actions">
        <template v-if="activeSection === 'guests'">
          <el-button :icon="Upload" @click="openGuestImportDialog">导入 Excel</el-button>
          <el-button :icon="Download" :loading="exporting" @click="handleExportGuestStatusSheet">导出嘉宾状态表</el-button>
          <el-button type="primary" :icon="Plus" @click="openGuestCreateDialog">新增嘉宾</el-button>
        </template>
        <template v-else-if="activeSection === 'overview'">
          <el-button
            type="primary"
            plain
            :icon="Download"
            :loading="exporting"
            @click="handleExportCheckInSheet"
          >
            导出签到表
          </el-button>
          <el-tag type="success">签到 {{ checkedCount }}/{{ totalGuestCount }}</el-tag>
        </template>
      </div>
      </div>

    <el-alert v-if="!session.admin" class="top-gap" type="warning" :closable="false" title="请先完成管理员登录后再查看和编辑会议。" />

    <el-tabs v-if="session.admin" v-model="activeSection" class="admin-detail-tabs">
      <el-tab-pane label="数据总览" name="overview">
        <section class="admin-overview-grid">
          <article class="admin-stat-card">
            <span>嘉宾总数</span>
            <strong>{{ totalGuestCount }}</strong>
            <small>已录入当前会议</small>
          </article>
          <article class="admin-stat-card">
            <span>已签到</span>
            <strong>{{ checkedCount }}</strong>
            <small>现场已完成签到</small>
          </article>
          <article class="admin-stat-card">
            <span>待签到</span>
            <strong>{{ Math.max(totalGuestCount - checkedCount, 0) }}</strong>
            <small>可继续核验入场</small>
          </article>
          <article class="admin-stat-card">
            <span>工作人员</span>
            <strong>{{ staff.length }}</strong>
            <small>已授权当前会议</small>
          </article>
        </section>

        <section class="admin-overview-content-grid">
          <article class="admin-panel admin-checkin-progress-panel">
            <div class="admin-panel__heading">
              <div>
                <h2>签到进度</h2>
                <p>实时更新工作人员录入的签到结果。</p>
              </div>
              <strong>{{ checkInRate }}%</strong>
            </div>
            <el-progress :percentage="checkInRate" :show-text="false" :stroke-width="12" color="#07563f" />
            <p class="admin-progress-caption">{{ checkedCount }} / {{ totalGuestCount }} 人已签到</p>
          </article>

          <article class="admin-panel admin-quick-actions-panel">
            <div class="admin-panel__heading"><h2>快捷操作</h2></div>
            <div class="admin-quick-actions">
              <button type="button" @click="activeSection = 'guests'">新增或查看嘉宾</button>
              <button type="button" @click="activeSection = 'fields'">配置嘉宾字段</button>
              <button type="button" @click="activeSection = 'assistant'">设置会议服务</button>
              <button type="button" @click="activeSection = 'staff'">维护工作人员</button>
            </div>
          </article>

          <article class="admin-panel admin-recent-checkin-panel">
            <div class="admin-panel__heading">
              <div>
                <h2>最近签到动态</h2>
                <p>显示最近完成的现场签到。</p>
              </div>
              <el-button link type="primary" @click="activeSection = 'checkins'">查看全部</el-button>
            </div>
            <el-empty v-if="!checkInLoading && checkIns.length === 0" description="暂无签到记录" :image-size="72" />
            <div v-else class="admin-recent-checkin-list">
              <article v-for="record in checkIns.slice(0, 4)" :key="`${record.guestId}-${record.checkedInAt}`">
                <span>{{ record.guestName.slice(0, 1) }}</span>
                <strong>{{ record.guestName }}</strong>
                <em>{{ record.method === 'scan' ? '扫码' : '人工' }}</em>
                <small>{{ formatDate(record.checkedInAt) }}</small>
              </article>
            </div>
          </article>
        </section>
      </el-tab-pane>
      <el-tab-pane class="admin-tab-panel" label="编辑会议" name="edit">
        <div class="meeting-edit-page">
          <div class="meeting-edit-layout">
            <section class="meeting-edit-form-card" aria-label="会议信息表单">
              <div class="meeting-edit-section">
                <div class="meeting-edit-section-head">
                  <div class="meeting-edit-section-index">01</div>
                  <div>
                    <h2>基础信息</h2>
                  </div>
                </div>
                <div class="meeting-edit-grid">
                  <label class="meeting-edit-field meeting-edit-field--full">
                    <span class="meeting-edit-label-row">会议名称</span>
                    <el-input v-model="editForm.title" placeholder="请输入会议名称" maxlength="200" show-word-limit />
                  </label>
                  <label class="meeting-edit-field">
                    <span class="meeting-edit-label-row">会议地点</span>
                    <el-input v-model="editForm.location" placeholder="请输入会议地点" />
                  </label>
                  <div class="meeting-edit-field">
                    <span class="meeting-edit-label-row">导航位置</span>
                    <div class="meeting-edit-nav-control">
                      <div class="meeting-edit-nav-name">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                          <path d="M12 21s7-5.1 7-11a7 7 0 1 0-14 0c0 5.9 7 11 7 11Z" stroke="currentColor" stroke-width="1.8" />
                          <path d="M12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z" stroke="currentColor" stroke-width="1.8" />
                        </svg>
                        <span>{{ editForm.navigationName || '未设置，将按会议地点匹配' }}</span>
                      </div>
                      <div class="meeting-edit-nav-actions">
                        <el-button size="small" type="primary" plain @click="openLocationDialog">
                          {{ editForm.navigationName ? '更换' : '选择' }}
                        </el-button>
                        <el-button v-if="editForm.navigationName" size="small" @click="clearNavigationLocation">清除</el-button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="meeting-edit-section">
                <div class="meeting-edit-section-head">
                  <div class="meeting-edit-section-index">02</div>
                  <div>
                    <h2>时间安排</h2>
                  </div>
                </div>
                <div class="meeting-edit-grid">
                  <label class="meeting-edit-field">
                    <span class="meeting-edit-label-row">开始时间</span>
                    <el-input v-model="editForm.startTime" type="datetime-local" />
                  </label>
                  <label class="meeting-edit-field">
                    <span class="meeting-edit-label-row">结束时间</span>
                    <el-input v-model="editForm.endTime" type="datetime-local" />
                  </label>
                  <label class="meeting-edit-field meeting-edit-field--full">
                    <span class="meeting-edit-label-row">首页时间显示方式</span>
                    <el-select v-model="editForm.timeDisplayMode">
                      <el-option label="显示到上午/下午" value="day_period" />
                      <el-option label="显示到具体时间" value="time" />
                    </el-select>
                  </label>
                  <div class="meeting-edit-field">
                    <span class="meeting-edit-label-row">自主报名</span>
                    <div class="meeting-edit-switch-row">
                      <el-switch
                        v-model="editForm.registrationEnabled"
                        active-text="开放"
                        inactive-text="关闭"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div class="meeting-edit-section">
                <div class="meeting-edit-section-head">
                  <div class="meeting-edit-section-index">03</div>
                  <div>
                    <h2>会议说明</h2>
                  </div>
                </div>
                <label class="meeting-edit-field meeting-edit-field--full">
                  <span class="meeting-edit-label-row">说明内容</span>
                  <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="请输入会议说明" maxlength="200" show-word-limit />
                </label>
              </div>

              <footer class="meeting-edit-form-footer">
                <p v-if="saveMessage" class="meeting-save-message" :class="`is-${saveMessageType}`">{{ saveMessage }}</p>
                <div class="meeting-edit-form-actions">
                  <el-button @click="resetEditForm">重置</el-button>
                  <el-button type="primary" :loading="saving" @click="saveMeeting">保存会议信息</el-button>
                </div>
              </footer>
            </section>

            <aside class="meeting-edit-side" aria-label="会议入口">
              <section class="meeting-edit-share-card">
                <div class="meeting-edit-side-head">
                  <div>
                    <div class="meeting-edit-eyebrow">Access</div>
                    <h2>会议入口</h2>
                  </div>
                  <span v-if="editForm.status === 'published'" class="meeting-edit-publish-badge">已发布</span>
                  <span v-else-if="editForm.status === 'ended'" class="meeting-edit-publish-badge is-ended">已结束</span>
                  <span v-else class="meeting-edit-publish-badge is-pending">待发布</span>
                </div>

                <div v-if="editForm.status === 'published'" class="meeting-edit-link-box">
                  <span>公开访问链接</span>
                  <div class="meeting-edit-link-row">
                    <el-input
                      v-model="publicUrlEdit"
                      placeholder="如 https://cssat.wenguang.top"
                      class="meeting-edit-link-input"
                      clearable
                    />
                    <el-button size="small" type="primary" plain @click="copyMeetingEntryUrl">复制</el-button>
                  </div>
                  <code class="meeting-edit-link-preview" :title="meetingEntryUrl">
                    {{ meetingEntryUrl }}
                  </code>
                </div>
                <div v-else class="meeting-edit-link-box meeting-edit-link-box--empty">
                  <span>发布后启用公开访问链接</span>
                </div>

                <div class="meeting-edit-qr-panel">
                  <div class="meeting-edit-qr-frame" aria-label="会议入口二维码">
                    <img v-if="meetingQrCode" :src="meetingQrCode" alt="会议入口二维码" />
                    <span v-else class="meeting-edit-qr-placeholder">{{ qrPlaceholderText }}</span>
                  </div>
                  <div class="meeting-edit-qr-copy">
                    <strong>嘉宾扫码进入</strong>
                    <el-button
                      size="small"
                      type="primary"
                      :disabled="!meetingEntryUrl"
                      :loading="regeneratingQr"
                      @click="regenerateMeetingEntryQrCode"
                    >
                      {{ meetingQrCode ? '重新生成二维码' : '生成二维码' }}
                    </el-button>
                    <el-button
                      v-if="meetingQrCode"
                      size="small"
                      :disabled="!meetingQrCode"
                      @click="downloadMeetingQrCode"
                    >
                      下载二维码
                    </el-button>
                  </div>
                </div>

                <footer class="meeting-edit-share-footer">
                  <el-button
                    v-if="editForm.status !== 'ended'"
                    :type="editForm.status === 'published' ? 'default' : 'primary'"
                    :plain="editForm.status === 'published'"
                    style="width: 100%"
                    @click="toggleMeetingPublishStatus"
                  >
                    {{ editForm.status === 'published' ? '撤回为草稿' : '发布会议' }}
                  </el-button>
                </footer>
              </section>
            </aside>
          </div>

          <el-dialog v-model="locationDialogVisible" title="选择导航位置" width="min(680px, calc(100% - 32px))">
            <div class="action-row">
              <el-input v-model="locationSearchQuery" placeholder="输入场馆、学校、酒店或详细地址" @keyup.enter="searchLocationOptions" />
              <el-button type="primary" :loading="locationSearching" @click="searchLocationOptions">搜索</el-button>
            </div>
            <el-alert v-if="locationSearchError" class="top-gap" type="error" :closable="false" :title="locationSearchError" />
            <el-empty v-else-if="!locationSearching && locationOptions.length === 0" description="输入地点关键词后搜索" />
            <div v-else class="location-option-list">
              <button
                v-for="option in locationOptions"
                :key="option.poiId || `${option.longitude}-${option.latitude}`"
                type="button"
                class="location-option-card"
                @click="selectLocationOption(option)"
              >
                <strong>{{ option.name }}</strong>
                <span>{{ option.district }}{{ option.address }}</span>
              </button>
            </div>
          </el-dialog>
        </div>
      </el-tab-pane>
      <el-tab-pane class="admin-tab-panel" label="嘉宾" name="guests">
        <section class="admin-guest-filter-panel">
          <el-select v-model="guestStatusFilter" aria-label="嘉宾状态筛选" class="admin-guest-filter-select">
            <el-option label="全部状态" value="all" />
            <el-option label="待审核" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已录入" value="entered" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
          <el-select v-model="guestCheckInFilter" aria-label="嘉宾签到筛选" class="admin-guest-filter-select">
            <el-option label="全部签到" value="all" />
            <el-option label="已签到" value="checked" />
            <el-option label="未签到" value="unchecked" />
          </el-select>
          <el-input v-model="guestSearchKeyword" class="admin-guest-filter-search" placeholder="搜索姓名 / 手机号 / 单位 / 职务" clearable />
        </section>
        <el-alert v-if="guestApplicationError" class="top-gap" type="error" :closable="false" :title="guestApplicationError" />
        <section class="admin-guest-list-panel">
        <el-table :data="filteredGuestManagementRows" row-key="id">
          <el-table-column prop="name" label="姓名" min-width="120" />
          <el-table-column prop="phone" label="手机号" min-width="135" />
          <el-table-column prop="organization" label="单位" min-width="160" show-overflow-tooltip />
          <el-table-column prop="title" label="职务" min-width="130" show-overflow-tooltip />
          <el-table-column label="来源" min-width="110"><template #default="{ row }">{{ guestSourceText(row.source) }}</template></el-table-column>
          <el-table-column label="状态" min-width="100"><template #default="{ row }"><el-tag :type="guestManagementStatusTagType(row.status)">{{ guestManagementStatusText(row.status) }}</el-tag></template></el-table-column>
          <el-table-column label="签到" min-width="100">
            <template #default="{ row }">
              <span class="admin-guest-checkin-text">{{ row.recordType === 'application' ? '—' : row.checkedIn ? '已签到' : '未签到' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right"><template #default="{ row }">
            <template v-if="row.recordType === 'application' && row.status === 'pending'">
              <el-button size="small" type="primary" :loading="reviewingApplicationId === row.application?.id" @click="reviewGuestApplication(row.application!, 'approved')">通过</el-button>
              <el-button size="small" :disabled="reviewingApplicationId === row.application?.id" @click="reviewGuestApplication(row.application!, 'rejected')">拒绝</el-button>
            </template>
            <template v-else>
              <el-button size="small" link @click="showGuestDetail(row.guest!)">查看</el-button>
              <el-button size="small" link type="primary" @click="openGuestEditDialog(row.guest!)">编辑</el-button>
              <el-button size="small" link type="danger" @click="handleDeleteGuest(row.guest!)">删除</el-button>
            </template>
          </template></el-table-column>
        </el-table>
        </section>
        <el-dialog v-model="guestImportDialogVisible" title="导入 Excel 嘉宾名单" width="min(560px, calc(100% - 32px))" align-center>
          <div class="admin-import-dialog__guide">
            <strong>按模板整理名单后上传</strong>
            <p>文件首行必须包含“姓名”和“手机号”列，系统会保留合法行并反馈错误行。</p>
          </div>
          <div class="admin-import-dialog__actions">
            <el-button @click="downloadGuestImportTemplate">下载 Excel 模板</el-button>
            <el-button type="primary" :loading="importing" @click="openGuestImportFilePicker">选择文件并导入</el-button>
            <input ref="guestImportInput" class="visually-hidden" type="file" accept=".xlsx" @change="handleGuestImportFileChange" />
          </div>
          <el-alert v-if="importMessage" class="top-gap" :type="importMessageType" :closable="false" :title="importMessage" />
        </el-dialog>
        <el-dialog v-model="guestCreateDialogVisible" title="新增嘉宾" width="min(620px, calc(100% - 32px))" align-center>
          <el-form label-position="top" @submit.prevent>
            <div class="form-grid"><el-form-item label="姓名" required><el-input v-model="guestForm.name" /></el-form-item><el-form-item label="手机号" required><el-input v-model="guestForm.phone" /></el-form-item></div>
            <div class="form-grid"><el-form-item label="单位"><el-input v-model="guestForm.organization" /></el-form-item><el-form-item label="职务"><el-input v-model="guestForm.title" /></el-form-item></div>
            <div class="form-grid"><el-form-item label="身份"><el-input v-model="guestForm.tag" /></el-form-item><el-form-item label="座位"><el-input v-model="guestForm.seat" /></el-form-item></div>
            <div v-if="enabledDynamicGuestFields.length" class="form-grid guest-dynamic-fields">
              <el-form-item v-for="field in enabledDynamicGuestFields" :key="field.key" :label="field.label" :required="field.required">
                <el-input v-model="guestForm.values[field.key]" />
              </el-form-item>
            </div>
            <div class="action-row"><el-button @click="guestCreateDialogVisible = false">取消</el-button><el-button type="primary" :loading="creatingGuest" @click="handleCreateGuest">保存嘉宾</el-button></div>
          </el-form>
        </el-dialog>
        <el-dialog v-model="guestEditDialogVisible" title="编辑嘉宾信息" width="min(620px, calc(100% - 32px))" align-center>
          <el-form v-loading="guestEditLoading" label-position="top" @submit.prevent>
            <div class="form-grid"><el-form-item label="姓名" required><el-input v-model="guestEditForm.name" /></el-form-item><el-form-item label="手机号" required><el-input v-model="guestEditForm.phone" /></el-form-item></div>
            <div class="form-grid"><el-form-item label="单位"><el-input v-model="guestEditForm.organization" /></el-form-item><el-form-item label="职务"><el-input v-model="guestEditForm.title" /></el-form-item></div>
            <div class="form-grid"><el-form-item label="身份"><el-input v-model="guestEditForm.tag" /></el-form-item><el-form-item label="座位"><el-input v-model="guestEditForm.seat" /></el-form-item></div>
            <div v-if="enabledDynamicGuestFields.length" class="form-grid guest-dynamic-fields">
              <el-form-item v-for="field in enabledDynamicGuestFields" :key="field.key" :label="field.label" :required="field.required">
                <el-input v-model="guestEditForm.values[field.key]" />
              </el-form-item>
            </div>
            <div class="action-row"><el-button @click="guestEditDialogVisible = false">取消</el-button><el-button type="primary" :loading="updatingGuest" @click="handleUpdateGuest">保存修改</el-button></div>
          </el-form>
        </el-dialog>
        <el-dialog v-model="guestDetailDialogVisible" title="嘉宾信息" width="min(420px, calc(100% - 32px))" align-center>
          <div v-loading="guestDetailLoading" class="guest-detail-content">
            <dl v-if="selectedGuest" class="info-list"><dt>姓名</dt><dd>{{ selectedGuest.name }}</dd><dt>手机号</dt><dd>{{ selectedGuest.phone }}</dd><dt>单位</dt><dd>{{ selectedGuest.organization || '—' }}</dd><dt>职务</dt><dd>{{ selectedGuest.title || '—' }}</dd><dt>身份</dt><dd>{{ selectedGuest.tag || '—' }}</dd><dt>座位</dt><dd>{{ selectedGuest.seat || '—' }}</dd><template v-for="item in selectedGuestDynamicRows" :key="item.key"><dt>{{ item.label }}</dt><dd>{{ item.value || '—' }}</dd></template></dl>
            <img v-if="guestQrCode" class="meeting-entry-qr" :src="guestQrCode" alt="嘉宾签到二维码" />
          </div>
        </el-dialog>
      </el-tab-pane>
      <el-tab-pane class="admin-tab-panel" label="字段" name="fields">
        <el-alert type="info" :closable="false" title="姓名和手机号固定用于身份核验。可配置字段是否必填、是否出现在报名表单、嘉宾个人信息页，以及是否启用。" />
        <div class="action-row top-gap">
          <el-button @click="addGuestFieldDraft">新增字段</el-button>
          <el-button :disabled="!fieldsChanged" @click="resetGuestFieldDrafts(fields, savedVisibleGuestFieldKeys, savedGuestRegistrationSettings)">重置</el-button>
          <el-button type="primary" :loading="savingGuestFields" :disabled="!fieldsChanged" @click="saveGuestFields">保存字段</el-button>
        </div>
        <el-alert v-if="guestFieldMessage" class="top-gap" :type="guestFieldMessageType" :closable="false" :title="guestFieldMessage" />
        <h3 class="guest-field-section-title">固定嘉宾信息</h3>
        <el-table :data="fixedGuestFieldDrafts" row-key="key">
          <el-table-column prop="label" label="字段名称" min-width="180" />
          <el-table-column label="必填" width="110"><template #default="{ row }"><el-switch v-model="row.required" :disabled="row.loginRequired" /></template></el-table-column>
          <el-table-column label="报名表单" width="130"><template #default="{ row }"><el-switch v-model="row.registrationVisible" :disabled="row.loginRequired" /></template></el-table-column>
          <el-table-column label="个人信息页" width="140"><template #default="{ row }"><el-switch v-model="row.visibleToGuest" :disabled="!row.isEnabled" /></template></el-table-column>
          <el-table-column label="启用" width="110"><template #default="{ row }"><el-switch v-model="row.isEnabled" :disabled="row.loginRequired" /></template></el-table-column>
        </el-table>
        <h3 class="guest-field-section-title">扩展嘉宾信息</h3>
        <el-table class="top-gap" :data="guestFieldDrafts" row-key="clientId">
          <el-table-column label="字段名称" min-width="180"><template #default="{ row }"><el-input v-model="row.label" placeholder="例如：饮食偏好" /></template></el-table-column>
          <el-table-column label="必填" width="110"><template #default="{ row }"><el-switch v-model="row.required" /></template></el-table-column>
          <el-table-column label="报名表单" width="130"><template #default="{ row }"><el-switch v-model="row.visibleToGuest" :disabled="!row.isEnabled" /></template></el-table-column>
          <el-table-column label="个人信息页" width="140"><template #default="{ row }"><el-switch v-model="row.profileVisible" :disabled="!row.isEnabled" /></template></el-table-column>
          <el-table-column label="启用" width="110"><template #default="{ row }"><el-switch v-model="row.isEnabled" /></template></el-table-column>
          <el-table-column label="操作" width="100"><template #default="{ $index }"><el-button type="danger" link @click="removeGuestFieldDraft($index)">删除</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane class="admin-tab-panel" label="会议助手" name="assistant">
        <el-alert type="info" :closable="false" title="每项功能由管理员编辑并独立发布；未发布时，嘉宾点击后会看到对应提醒。" />
        <el-alert v-if="assistantError" class="top-gap" type="error" :closable="false" :title="assistantError" />
        <el-table v-loading="assistantLoading" class="top-gap" :data="assistantFeatures" row-key="key">
          <el-table-column prop="title" label="功能" width="140" />
          <el-table-column prop="description" label="入口说明" min-width="220" />
          <el-table-column label="访问权限" width="150"><template #default="{ row }"><el-tag :type="row.accessLevel === 'public' ? 'success' : 'info'">{{ row.accessLevel === 'public' ? '公开可见' : '仅登录嘉宾' }}</el-tag></template></el-table-column>
          <el-table-column label="发布状态" width="110"><template #default="{ row }"><el-tag :type="row.isPublished ? 'success' : 'info'">{{ row.isPublished ? '已发布' : '未发布' }}</el-tag></template></el-table-column>
          <el-table-column prop="unpublishedMessage" label="未发布提醒" min-width="260" show-overflow-tooltip />
          <el-table-column label="操作" width="100"><template #default="{ row }"><el-button size="small" @click="openAssistantEditDialog(row)">编辑</el-button></template></el-table-column>
        </el-table>
        <el-dialog
          v-model="assistantEditDialogVisible"
          :title="`编辑${selectedAssistantFeature?.title ?? '会议助手'}`"
          :width="selectedAssistantFeature?.key === 'agenda' ? 'min(1180px, calc(100% - 32px))' : selectedAssistantFeature?.key === 'manual' ? 'min(780px, calc(100% - 32px))' : 'min(620px, calc(100% - 32px))'"
          class="assistant-edit-dialog"
        >
          <el-form label-position="top" @submit.prevent>
            <el-form-item label="发布状态"><el-switch v-model="assistantEditForm.isPublished" active-text="已发布" inactive-text="未发布" /></el-form-item>
            <el-form-item label="访问权限">
              <el-radio-group v-model="assistantEditForm.accessLevel">
                <el-radio value="public">公开可见</el-radio>
                <el-radio value="guest">仅登录嘉宾可见</el-radio>
              </el-radio-group>
              <div class="el-form-item__help">公开可见只影响已发布内容，未发布草稿不会公开。</div>
            </el-form-item>
            <AdminAgendaEditor
              v-if="selectedAssistantFeature?.key === 'agenda'"
              v-model="assistantEditForm.content"
              :meeting-start-time="meeting?.startTime"
            />
            <AdminMeetingMaterialsEditor
              v-else-if="selectedAssistantFeature?.key === 'manual' && meeting"
              :meeting-id="meeting.id"
              @count-change="assistantMaterialCount = $event"
            />
            <el-form-item v-else-if="selectedAssistantFeature?.key === 'route'" label="路线说明">
              <MeetingMaterialRichTextEditor
                v-model="assistantEditForm.content"
                label="路线说明"
                placeholder="请输入路线说明，可使用段落、加粗、列表和缩进"
              />
            </el-form-item>
            <template v-else-if="selectedAssistantFeature?.key === 'contact'">
              <div class="admin-contact-qr-panel">
                <div class="admin-contact-qr-panel__fields">
                  <el-form-item label="二维码上方文字">
                    <el-input v-model="assistantEditForm.contactQrTitle" maxlength="100" placeholder="会务二维码" />
                  </el-form-item>
                  <div class="admin-contact-qr-panel__actions">
                    <input
                      ref="contactQrInput"
                      class="admin-contact-qr-panel__input"
                      type="file"
                      accept="image/png,image/jpeg,image/jpg"
                      @change="handleContactQrFileChange"
                    >
                    <el-button type="primary" plain :loading="uploadingContactQr" @click="selectContactQrFile">上传二维码</el-button>
                    <el-button
                      v-if="selectedAssistantFeature.contactQrOriginalFilename"
                      type="danger"
                      plain
                      :loading="deletingContactQr"
                      @click="removeContactQrImage"
                    >
                      删除二维码
                    </el-button>
                  </div>
                </div>
                <div class="admin-contact-qr-panel__preview">
                  <img v-if="contactQrPreviewUrl" :src="contactQrPreviewUrl" alt="会务二维码预览">
                  <span v-else>未上传二维码</span>
                </div>
              </div>
              <div class="admin-contact-table-panel">
                <div class="admin-contact-table-panel__heading">
                  <span>会务联系人</span>
                  <el-button type="primary" plain size="small" @click="addContactPerson">添加联系人</el-button>
                </div>
                <el-table
                  :data="assistantEditForm.contacts"
                  class="admin-contact-table"
                  row-key="__rowKey"
                  :show-header="true"
                  :border="false"
                  empty-text="暂无联系人，请点击上方添加"
                >
                  <el-table-column label="姓名" min-width="140">
                    <template #default="{ row }">
                      <el-input v-model="row.name" class="admin-contact-input" placeholder="王会务" />
                    </template>
                  </el-table-column>
                  <el-table-column label="职责" min-width="160">
                    <template #default="{ row }">
                      <el-input v-model="row.role" class="admin-contact-input" placeholder="会务总协调" />
                    </template>
                  </el-table-column>
                  <el-table-column label="电话" min-width="160">
                    <template #default="{ row }">
                      <el-input v-model="row.phone" class="admin-contact-input" placeholder="13800000000" />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="72" align="center">
                    <template #default="{ $index }">
                      <el-button type="danger" link size="small" @click="removeContactPerson($index)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>
            <el-form-item v-else label="功能内容"><el-input v-model="assistantEditForm.content" type="textarea" :rows="7" placeholder="请输入发布后向嘉宾展示的内容" /></el-form-item>
            <el-form-item label="未发布提醒"><el-input v-model="assistantEditForm.unpublishedMessage" type="textarea" :rows="3" placeholder="请输入功能尚未发布时向嘉宾展示的提醒" /></el-form-item>
            <div class="action-row"><el-button type="primary" :loading="savingAssistantFeature" @click="saveAssistantFeature">保存配置</el-button></div>
          </el-form>
        </el-dialog>
      </el-tab-pane>
      <el-tab-pane class="admin-tab-panel" label="工作人员" name="staff">
        <el-form class="edit-form" label-position="top" @submit.prevent>
          <el-form-item label="登录账号"><el-input v-model="staffForm.account" placeholder="请输入工作人员账号（字母开头，3-100 位）" /></el-form-item>
          <el-form-item label="初始密码"><el-input v-model="staffForm.initialPassword" type="password" show-password placeholder="至少 8 位" /></el-form-item>
          <el-form-item label="显示名（选填）"><el-input v-model="staffForm.displayName" placeholder="如：会务组小张；留空则显示账号" maxlength="100" /></el-form-item>
          <div class="action-row"><el-button type="primary" :loading="creatingStaff" @click="handleCreateStaff">创建并授权当前会议</el-button></div>
          <el-alert v-if="staffMessage" class="top-gap" :type="staffMessageType" :closable="false" :title="staffMessage" />
        </el-form>
        <el-table :data="staff" row-key="id">
          <el-table-column prop="account" label="账号" />
          <el-table-column label="显示名" min-width="130"><template #default="{ row }">{{ row.displayName || row.account }}</template></el-table-column>
          <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="row.isActive ? 'success' : 'info'">{{ row.isActive ? '启用' : '停用' }}</el-tag></template></el-table-column>
          <el-table-column label="操作" width="180"><template #default="{ row }"><el-button size="small" @click="openStaffEditDialog(row)">编辑</el-button><el-button size="small" type="danger" plain @click="handleRemoveStaff(row)">解除授权</el-button></template></el-table-column>
        </el-table>
        <el-dialog v-model="staffEditDialogVisible" title="编辑工作人员" width="min(520px, calc(100% - 32px))">
          <el-form label-position="top" @submit.prevent>
            <el-form-item label="显示名"><el-input v-model="staffEditForm.displayName" placeholder="留空则显示账号" maxlength="100" /></el-form-item>
            <el-form-item label="账号状态"><el-switch v-model="staffEditForm.isActive" active-text="启用" inactive-text="停用" /></el-form-item>
            <el-form-item label="重置密码"><el-input v-model="staffEditForm.newPassword" type="password" show-password placeholder="不修改请留空；新密码至少 8 位" /></el-form-item>
            <div class="action-row"><el-button type="primary" :loading="savingStaff" @click="handleUpdateStaff">保存</el-button></div>
          </el-form>
        </el-dialog>
      </el-tab-pane>
      <el-tab-pane class="admin-tab-panel" label="签到管理" name="checkins">
        <el-alert v-if="checkInError" type="error" :closable="false" :title="checkInError" />
        <section class="checkin-management-page top-gap">
          <section id="checkin-session-list" class="checkin-compact-grid">
            <article class="admin-panel checkin-session-panel">
              <div class="admin-panel__heading checkin-panel-heading">
                <div>
                  <h2>签到场次</h2>
                  <p>{{ checkInModeMeta.label }}｜{{ checkInModeCountHint }}</p>
                </div>
                <div class="checkin-session-actions">
                  <el-button
                    plain
                    type="primary"
                    :icon="Refresh"
                    :disabled="dateSessionGenerationSummary.disabled && checkInMode === 'date'"
                    :loading="generatingDateSessions"
                    @click="generateDateCheckInSessions"
                  >
                    按日期生成
                  </el-button>
                  <el-button
                    v-if="checkInMode === 'date' && checkInManualDefaultSessionId"
                    plain
                    :icon="Refresh"
                    @click="restoreDateAutoDefault"
                  >
                    恢复自动切换
                  </el-button>
                  <el-button plain type="primary" :icon="Plus" @click="prepareCustomCheckInSession">新增场次</el-button>
                  <el-input
                    v-model="checkInSessionKeyword"
                    class="checkin-session-search"
                    :prefix-icon="Search"
                    placeholder="搜索场次名称"
                    clearable
                  />
                </div>
              </div>

              <section v-loading="checkInSessionLoading" class="checkin-session-status-list">
                <article
                  v-for="sessionItem in filteredCheckInSessions"
                  :key="sessionItem.id"
                  class="checkin-session-status-item"
                  :class="{ 'is-active': sessionItem.isDefault }"
                >
                  <div class="checkin-session-status-item__default">
                    <button
                      type="button"
                      class="checkin-default-dot"
                      :class="{ 'is-active': sessionItem.isDefault }"
                      :aria-label="sessionItem.isDefault ? '当前默认场次' : '设为默认场次'"
                      :disabled="sessionItem.isDefault"
                      @click="setDefaultCheckInSession(sessionItem)"
                    >
                      <span />
                    </button>
                  </div>
                  <div class="checkin-session-status-item__main">
                    <div class="checkin-session-status-item__title">
                      <strong>{{ sessionItem.title }}</strong>
                      <el-tag type="info" size="small">{{ sessionTypeText(sessionItem) }}</el-tag>
                    </div>
                    <small>{{ sessionTimeText(sessionItem) }}</small>
                  </div>
                  <div class="checkin-session-progress">
                    <el-progress :percentage="sessionProgressPercentage(sessionItem)" :show-text="false" :stroke-width="6" />
                    <span>{{ sessionProgressText(sessionItem) }}</span>
                  </div>
                  <div class="checkin-session-status-item__counts">
                    <span>已签 <strong>{{ sessionRecordCount(sessionItem) }}</strong></span>
                    <span>待签 <strong>{{ sessionUncheckedCount(sessionItem) }}</strong></span>
                  </div>
                  <div class="checkin-session-status-item__actions">
                    <el-button size="small" link @click="editCheckInSession(sessionItem)">编辑</el-button>
                    <el-button
                      size="small"
                      link
                      type="danger"
                      :loading="deletingCheckInSessionId === sessionItem.id"
                      @click="confirmDeleteCheckInSession(sessionItem)"
                    >
                      删除
                    </el-button>
                  </div>
                </article>
                <el-empty v-if="!filteredCheckInSessions.length" description="暂无签到场次" :image-size="72" />
              </section>

              <div class="checkin-session-note">列表以签到状态为主；编辑、删除和排序能力作为后续管理操作收敛展示。</div>
            </article>

            <aside class="checkin-side-stack">
              <article class="admin-panel checkin-record-panel">
                <div class="admin-panel__heading checkin-panel-heading">
                  <div>
                    <h2>签到统计</h2>
                    <p>{{ selectedCheckInSession?.title || '未选择场次' }}｜签到人员列表</p>
                  </div>
                  <div class="checkin-record-heading-actions">
                    <el-select v-model="selectedCheckInSessionId" class="admin-checkin-session-select" placeholder="选择签到场次" @change="handleCheckInSessionSelect">
                      <el-option v-for="sessionItem in checkInSessions" :key="sessionItem.id" :label="sessionItem.title" :value="sessionItem.id" />
                    </el-select>
                    <el-button circle plain :icon="FullScreen" aria-label="放大查看签到明细" @click="openCheckInRecordDialog" />
                  </div>
                </div>
                <section class="checkin-record-stats">
                  <article>
                    <span>已签到</span>
                    <strong>{{ checkIns.length }}</strong>
                    <small>当前选中场次</small>
                  </article>
                  <article>
                    <span>待签到</span>
                    <strong>{{ Math.max(totalGuestCount - checkIns.length, 0) }}</strong>
                    <small>按当前场次计算</small>
                  </article>
                  <article>
                    <span>签到率</span>
                    <strong>{{ selectedSessionRate }}%</strong>
                    <small>{{ selectedCheckInSession?.title || '未选择' }}</small>
                  </article>
                </section>
                <section v-loading="checkInLoading" class="checkin-record-preview">
                  <article v-for="record in checkIns" :key="record.guestId" class="checkin-record-preview-item">
                    <div>
                      <strong>{{ record.guestName }}</strong>
                      <small>{{ record.phone }}</small>
                    </div>
                    <div>
                      <span>{{ formatDate(record.checkedInAt) }}</span>
                      <small>{{ record.method === 'scan' ? '扫码' : '人工' }}｜{{ record.staffName }}</small>
                    </div>
                  </article>
                  <el-empty v-if="!checkIns.length && !checkInLoading" description="当前场次暂无签到人员" :image-size="54" />
                </section>
              </article>

              <article class="admin-panel checkin-comparison-panel">
                <div class="admin-panel__heading checkin-comparison-heading">
                  <div>
                    <h2>场次对比</h2>
                    <p>
                      {{
                        checkInComparison
                          ? `当前场次“${selectedCheckInSession?.title || '未选择'}”与“${checkInComparison.previousSessionTitle}”对比`
                          : '首个场次暂无前序对比。'
                      }}
                    </p>
                  </div>
                </div>
                <div v-if="checkInComparison" class="checkin-comparison-cards">
                  <section class="checkin-comparison-card is-added">
                    <span>新增：本场已签到、对比场次未签到</span>
                    <strong>{{ checkInComparison.addedGuests.length }} 人</strong>
                    <ul>
                      <li v-for="guest in checkInComparison.addedGuests.slice(0, 3)" :key="guest.guestId">
                        <span>{{ guest.guestName }}</span>
                        <small>{{ guest.phone }}</small>
                      </li>
                    </ul>
                    <small v-if="!checkInComparison.addedGuests.length">暂无新增人员</small>
                  </section>
                  <section class="checkin-comparison-card is-removed">
                    <span>减少：对比场次已签到、本场未签到</span>
                    <strong>{{ checkInComparison.removedGuests.length }} 人</strong>
                    <ul>
                      <li v-for="guest in checkInComparison.removedGuests.slice(0, 3)" :key="guest.guestId">
                        <span>{{ guest.guestName }}</span>
                        <small>{{ guest.phone }}</small>
                      </li>
                    </ul>
                    <small v-if="!checkInComparison.removedGuests.length">暂无减少人员</small>
                  </section>
                </div>
                <el-empty v-else description="暂无场次对比" :image-size="64" />
              </article>
            </aside>
          </section>

          <el-dialog
            v-model="checkInSessionDialogVisible"
            :title="checkInSessionForm.id ? '编辑签到场次' : '新增签到场次'"
            width="min(760px, calc(100% - 32px))"
            @closed="resetCheckInSessionForm"
          >
            <div class="checkin-edit-dialog__head">
              <div>
                <p>日期场次和自定义场次使用同一套字段，默认场次可在表格中随时调整。</p>
              </div>
            </div>
            <el-form class="checkin-session-form" label-position="top" @submit.prevent>
              <el-form-item label="场次名称">
                <el-input v-model="checkInSessionForm.title" placeholder="例如：第二天签到" maxlength="100" />
              </el-form-item>
              <el-form-item label="开始时间">
                <el-input v-model="checkInSessionForm.startsAt" type="datetime-local" />
              </el-form-item>
              <el-form-item label="结束时间">
                <el-input v-model="checkInSessionForm.endsAt" type="datetime-local" />
              </el-form-item>
              <el-form-item label="场次说明">
                <el-input v-model="checkInSessionForm.description" placeholder="可填写地点、对象或注意事项" maxlength="1000" />
              </el-form-item>
              <el-form-item label="默认场次">
                <el-switch v-model="checkInSessionForm.isDefault" active-text="设为默认" inactive-text="普通场次" />
              </el-form-item>
              <div class="checkin-session-form__actions">
                <el-button @click="closeCheckInSessionDialog">取消</el-button>
                <el-button type="primary" :loading="savingCheckInSession" @click="saveCheckInSession">
                  {{ checkInSessionForm.id ? '保存场次' : '新增场次' }}
                </el-button>
              </div>
            </el-form>
          </el-dialog>

          <el-dialog
            v-model="checkInRecordDialogVisible"
            :title="`${selectedCheckInSession?.title || '当前场次'}签到明细`"
            width="min(900px, calc(100% - 32px))"
          >
            <section class="checkin-record-dialog-summary">
              <article>
                <span>已签到</span>
                <strong>{{ checkIns.length }}</strong>
              </article>
              <article>
                <span>待签到</span>
                <strong>{{ Math.max(totalGuestCount - checkIns.length, 0) }}</strong>
              </article>
              <article>
                <span>签到率</span>
                <strong>{{ selectedSessionRate }}%</strong>
              </article>
            </section>
            <el-table v-loading="checkInLoading" class="admin-data-table top-gap" :data="checkIns" row-key="guestId" max-height="460">
              <el-table-column label="签到时间" width="180"><template #default="{ row }">{{ formatDate(row.checkedInAt) }}</template></el-table-column>
              <el-table-column prop="guestName" label="嘉宾" min-width="120" />
              <el-table-column prop="phone" label="手机号" width="150" />
              <el-table-column prop="staffName" label="工作人员" min-width="130" />
              <el-table-column label="方式" width="100"><template #default="{ row }">{{ row.method === 'scan' ? '扫码' : '人工' }}</template></el-table-column>
            </el-table>
          </el-dialog>

        </section>
      </el-tab-pane>
      </el-tabs>
    </section>
  </AdminWorkspaceLayout>
  <section v-else class="page">
    <el-skeleton v-if="detailLoading" :rows="6" animated />
    <template v-else>
      <el-alert type="error" :closable="false" :title="detailError || '会议详情加载失败。'" />
      <div class="action-row top-gap"><el-button @click="goMeetings">返回会议管理</el-button></div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Download, FullScreen, Plus, Refresh, Search, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import QRCode from 'qrcode'

import {
  downloadAdminCheckInExport,
  downloadAdminGuestImportTemplate,
  downloadAdminGuestStatusExport,
  importAdminGuests,
} from '../../api/adminExcel'
import {
  createAdminCheckInSession,
  deleteAdminCheckInSession,
  getAdminCheckInSettings,
  getAdminCheckInSummary,
  listAdminCheckInSessions,
  updateAdminCheckInSettings,
  updateAdminCheckInSession,
} from '../../api/adminCheckIns'
import {
  createAdminGuest,
  deleteAdminGuest,
  getAdminGuestDisplayFields,
  getAdminGuest,
  getAdminGuestRegistrationSettings,
  listAdminGuestFields,
  listAdminGuests,
  replaceAdminGuestFields,
  replaceAdminGuestDisplayFields,
  replaceAdminGuestRegistrationSettings,
  updateAdminGuest,
  type AdminGuestRegistrationSettings,
  type AdminGuestFieldInput,
} from '../../api/adminGuests'
import {
  listAdminGuestApplications,
  reviewAdminGuestApplication,
  type AdminGuestApplication,
} from '../../api/adminGuestApplications'
import {
  getAdminMeeting,
  searchMeetingLocationOptions,
  updateAdminMeeting,
  type MeetingLocationOption,
} from '../../api/adminMeetings'
import {
  deleteAdminContactQr,
  fetchContactQrObjectUrl,
  listAdminMeetingAssistantFeatures,
  updateAdminMeetingAssistantFeature,
  uploadAdminContactQr,
} from '../../api/meetingAssistant'
import { createAdminStaff, listAdminStaff, removeAdminStaffAssignment, updateAdminStaff } from '../../api/adminStaff'
import { getApiErrorMessage } from '../../api/client'
import AdminAgendaEditor from '../../components/AdminAgendaEditor.vue'
import AdminMeetingMaterialsEditor from '../../components/AdminMeetingMaterialsEditor.vue'
import MeetingMaterialRichTextEditor from '../../components/MeetingMaterialRichTextEditor.vue'
import AdminWorkspaceLayout from '../../components/AdminWorkspaceLayout.vue'
import { useSessionStore } from '../../stores/session'
import { decodeMaterialRichContent, encodeMaterialRichContent } from '../../utils/materialRichText'
import type {
  AdminCheckInComparison,
  AdminCheckInRecord,
  CheckInMode,
  CheckInSession,
  Guest,
  GuestField,
  GuestImportInput,
  Meeting,
  MeetingAssistantAccessLevel,
  MeetingAssistantFeature,
  MeetingStatus,
  MeetingTimeDisplayMode,
  StaffUser,
} from '../../types'

interface GuestManagementRow {
  id: string
  recordType: 'guest' | 'application'
  name: string
  phone: string
  organization: string
  title: string
  source: Guest['source']
  status: 'pending' | 'approved' | 'entered' | 'rejected'
  checkedIn: boolean
  guest?: Guest
  application?: AdminGuestApplication
}

interface GuestFormState extends GuestImportInput {
  values: Record<string, string | null>
}

interface CheckInSessionFormState {
  id: string
  title: string
  description: string
  startsAt: string
  endsAt: string
  isDefault: boolean
}

interface DateSessionGenerationSummary {
  total: number
  existing: number
  missing: number
  label: string
  disabled: boolean
}

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const meeting = ref<Meeting>()
const detailLoading = ref(true)
const detailError = ref('')
const guests = ref<Guest[]>([])
const fields = ref<GuestField[]>([])
const fixedGuestFieldDrafts = ref([
  { key: 'name', label: '姓名', loginRequired: true, required: true, registrationVisible: true, visibleToGuest: true, isEnabled: true },
  { key: 'phone', label: '手机号', loginRequired: true, required: true, registrationVisible: true, visibleToGuest: true, isEnabled: true },
  { key: 'organization', label: '单位', loginRequired: false, required: false, registrationVisible: true, visibleToGuest: true, isEnabled: true },
  { key: 'title', label: '职务', loginRequired: false, required: false, registrationVisible: true, visibleToGuest: true, isEnabled: true },
  { key: 'tag', label: '身份', loginRequired: false, required: false, registrationVisible: false, visibleToGuest: true, isEnabled: true },
  { key: 'seat', label: '座位号', loginRequired: false, required: false, registrationVisible: false, visibleToGuest: true, isEnabled: true },
])
const guestFieldDrafts = ref<Array<AdminGuestFieldInput & { clientId: string; profileVisible: boolean }>>([])
const savedVisibleGuestFieldKeys = ref<string[]>([])
const savedGuestRegistrationSettings = ref<AdminGuestRegistrationSettings>({ fields: [], requiredFields: [], enabledFields: [] })
const savingGuestFields = ref(false)
const guestFieldMessage = ref('')
const guestFieldMessageType = ref<'success' | 'error' | 'info'>('success')
const staff = ref<StaffUser[]>([])
const checkInSessions = ref<CheckInSession[]>([])
const selectedCheckInSessionId = ref('')
const checkInMode = ref<CheckInMode>('single')
const checkInManualDefaultSessionId = ref('')
const checkInSessionKeyword = ref('')
const generatingDateSessions = ref(false)
const checkInSessionLoading = ref(false)
const savingCheckInSession = ref(false)
const deletingCheckInSessionId = ref('')
const checkInSessionDialogVisible = ref(false)
const checkInRecordDialogVisible = ref(false)
const checkInSessionForm = ref<CheckInSessionFormState>(createEmptyCheckInSessionForm())
const checkInComparison = ref<AdminCheckInComparison>()
const checkIns = ref<AdminCheckInRecord[]>([])
const checkInLoading = ref(false)
const checkInError = ref('')
const totalGuestCount = ref(0)
const assistantFeatures = ref<MeetingAssistantFeature[]>([])
const assistantLoading = ref(false)
const assistantError = ref('')
const saving = ref(false)
const exporting = ref(false)
const importing = ref(false)
const creatingStaff = ref(false)
const savingStaff = ref(false)
const savingAssistantFeature = ref(false)
const guestApplications = ref<AdminGuestApplication[]>([])
const guestApplicationError = ref('')
const reviewingApplicationId = ref('')
const guestStatusFilter = ref<'all' | 'pending' | 'approved' | 'entered' | 'rejected'>('all')
const guestCheckInFilter = ref<'all' | 'checked' | 'unchecked'>('all')
const guestSearchKeyword = ref('')
const selectedGuest = ref<Guest>()
const guestDetailDialogVisible = ref(false)
const guestDetailLoading = ref(false)
const guestQrCode = ref('')
const guestCreateDialogVisible = ref(false)
const creatingGuest = ref(false)
const guestForm = ref<GuestFormState>(createGuestFormState())
const editingGuest = ref<Guest>()
const guestEditDialogVisible = ref(false)
const guestEditLoading = ref(false)
const updatingGuest = ref(false)
const guestEditForm = ref<GuestFormState>(createGuestFormState())
const guestImportDialogVisible = ref(false)
const staffMessage = ref('')
const staffMessageType = ref<'success' | 'error'>('success')
const staffForm = ref({ account: '', initialPassword: '', displayName: '' })
const selectedStaff = ref<StaffUser>()
const staffEditDialogVisible = ref(false)
const staffEditForm = ref({ isActive: true, newPassword: '', displayName: '' })
const selectedAssistantFeature = ref<MeetingAssistantFeature>()
const assistantEditDialogVisible = ref(false)
const assistantMaterialCount = ref(0)
const contactQrInput = ref<HTMLInputElement>()
const contactQrPreviewUrl = ref('')
const uploadingContactQr = ref(false)
const deletingContactQr = ref(false)
const assistantEditForm = ref({
  content: '',
  unpublishedMessage: '',
  isPublished: false,
  accessLevel: 'guest' as MeetingAssistantAccessLevel,
  contactQrTitle: '会务二维码',
  contacts: [] as Array<{ __rowKey: string; name: string; role: string; phone: string }>,
})

/**
 * 生成联系人表格行的稳定键。
 *
 * 入参：无。
 * 返回值：string：用于 el-table row-key 的唯一字符串。
 * 异常：当前函数不主动抛出异常。
 */
function createContactRowKey(): string {
  return `contact-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

/**
 * 创建一行可编辑的空联系人。
 *
 * 入参：partial 为可选初始值。
 * 返回值：包含 rowKey 的联系人对象。
 * 异常：当前函数不主动抛出异常。
 */
function createContactRow(partial?: { name?: string; role?: string; phone?: string }): {
  __rowKey: string
  name: string
  role: string
  phone: string
} {
  return {
    __rowKey: createContactRowKey(),
    name: partial?.name ?? '',
    role: partial?.role ?? '',
    phone: partial?.phone ?? '',
  }
}
const guestImportInput = ref<HTMLInputElement>()
const importMessage = ref('')
const importMessageType = ref<'success' | 'warning' | 'error' | 'info'>('success')
const saveMessage = ref('')
const saveMessageType = ref<'success' | 'warning' | 'error' | 'info'>('success')
const editForm = ref({
  title: '',
  description: '',
  location: '',
  navigationName: '',
  navigationAddress: '',
  navigationLongitude: undefined as number | undefined,
  navigationLatitude: undefined as number | undefined,
  startTime: '',
  endTime: '',
  timeDisplayMode: 'day_period' as MeetingTimeDisplayMode,
  status: 'draft' as MeetingStatus,
  registrationEnabled: false,
  publicUrl: '',
})
const locationDialogVisible = ref(false)
const locationSearchQuery = ref('')
const locationSearching = ref(false)
const locationSearchError = ref('')
const locationOptions = ref<MeetingLocationOption[]>([])

/** 边栏中可编辑的公开访问链接：空时用默认地址生成二维码。 */
const publicUrlEdit = ref('')

const checkedCount = computed(() => checkIns.value.length)
const enabledDynamicGuestFields = computed(() => fields.value.filter((field) => field.isEnabled))
const selectedGuestDynamicRows = computed(() => enabledDynamicGuestFields.value.map((field) => ({
  key: field.key,
  label: field.label,
  value: selectedGuest.value?.values?.[field.key] ?? '',
})))
const guestFieldDefinitionsChanged = computed(() => JSON.stringify(guestFieldDrafts.value.map(({ clientId: _, profileVisible: __, ...field }) => field)) !== JSON.stringify(fields.value.map((field) => ({
  label: field.label,
  key: field.key,
  type: field.type,
  required: field.required,
  visibleToGuest: field.visibleToGuest,
  isEnabled: field.isEnabled,
}))))
const fixedGuestRegistrationSettingsChanged = computed(() => JSON.stringify(currentFixedGuestRegistrationSettings()) !== JSON.stringify(savedGuestRegistrationSettings.value))
const fieldsChanged = computed(() => guestFieldDefinitionsChanged.value || fixedGuestRegistrationSettingsChanged.value || JSON.stringify(selectedGuestDisplayFieldKeys()) !== JSON.stringify(savedVisibleGuestFieldKeys.value))
const publicAppBaseUrl = resolvePublicAppBaseUrl()
/** 完整访问链接：编辑框（base URL）后自动拼接 /meetings/{id}。 */
const meetingEntryUrl = computed(() => {
  if (!meeting.value) return ''
  const customBase = publicUrlEdit.value.trim()
  if (customBase) return `${customBase.replace(/\/+$/, '')}/meetings/${meeting.value.id}`
  if (!publicAppBaseUrl) return ''
  return `${publicAppBaseUrl.replace(/\/+$/, '')}/meetings/${meeting.value.id}`
})
const meetingQrCode = ref('')
const regeneratingQr = ref(false)
/** 编辑框为空时二维码占位文案（默认取当前浏览器访问的本机地址）。 */
const qrPlaceholderText = computed(() => {
  if (meeting.value) return '点击下方生成二维码'
  return '暂未生成'
})

/**
 * 默认公开访问地址：浏览器当前的 origin（如 http://192.168.10.171:5174），
 * 管理员可根据部署环境修改后保存到后端。
 */
function getDefaultPublicBaseUrl(): string {
  if (typeof window === 'undefined') return ''
  return window.location.origin.replace(/\/+$/, '')
}
/** 会议信息页副标题：地点 + 起止时间，与 HTML 设计稿描述一致。 */
const meetingSubtitle = computed(() => {
  if (!meeting.value) return ''
  const parts: string[] = []
  if (meeting.value.location) parts.push(meeting.value.location)
  const timeText = `${formatDate(meeting.value.startTime)} - ${formatDate(meeting.value.endTime)}`
  parts.push(timeText)
  return parts.join('｜')
})
const guestRows = computed(() => guests.value.map((guest) => ({
  ...guest,
  checkedIn: checkIns.value.some((record) => record.guestId === guest.id),
})))
const selectedCheckInSession = computed(() => checkInSessions.value.find((item) => item.id === selectedCheckInSessionId.value))
const checkInModeMeta = computed(resolveCheckInModeMeta)
const checkInModeCountHint = computed(resolveCheckInModeCountHint)
const filteredCheckInSessions = computed(filterCheckInSessions)
const dateSessionGenerationSummary = computed(resolveDateSessionGenerationSummary)
const selectedSessionRate = computed(resolveSelectedSessionRate)
const pendingGuestApplications = computed(() => guestApplications.value.filter((application) => application.status === 'pending'))
const guestManagementRows = computed(resolveGuestManagementRows)
const filteredGuestManagementRows = computed(filterGuestManagementRows)
const activeSection = computed({ get: resolveActiveSection, set: selectActiveSection })
const activeSectionTitle = computed(resolveActiveSectionTitle)
const checkInRate = computed(resolveCheckInRate)

const adminWorkspaceSections = new Set([
  'overview',
  'edit',
  'guests',
  'fields',
  'assistant',
  'staff',
  'checkins',
])

/**
 * 读取路由查询参数中的管理员工作台区块。
 *
 * 入参：无；函数读取当前路由的 `tab` 查询参数。
 * 返回值：string：已知区块标识原样返回，缺失或未知时返回“overview”。
 * 异常：当前函数不主动抛出异常。
 */
function resolveActiveSection(): string {
  const tab = String(route.query.tab || '')
  return adminWorkspaceSections.has(tab) ? tab : 'overview'
}

/**
 * 将管理员工作台区块同步到路由查询参数。
 *
 * 入参：section 为要展示的工作台区块标识，必填。
 * 返回值：void：使用 replace 更新 URL，不新增浏览器历史记录。
 * 异常：当前函数不主动抛出异常；未知区块会回退到“overview”。
 */
function selectActiveSection(section: string): void {
  const tab = adminWorkspaceSections.has(section) ? section : 'overview'
  if (tab === resolveActiveSection()) {
    return
  }
  void router.replace({ query: { ...route.query, tab } })
}

/**
 * 处理管理员工作台侧边栏发出的区块切换请求。
 *
 * 入参：section 为侧边栏菜单对应的工作台区块标识，必填。
 * 返回值：void：更新当前激活区块。
 * 异常：当前函数不主动抛出异常。
 */
function handleWorkspaceNavigation(section: string): void {
  selectActiveSection(section)
}

/**
 * 将当前工作台区块转换为页面标题。
 *
 * 入参：无；函数读取激活区块。
 * 返回值：string：适合页面标题展示的中文名称。
 * 异常：当前函数不主动抛出异常。
 */
function resolveActiveSectionTitle(): string {
  const titleMap: Record<string, string> = {
    overview: '数据总览',
    edit: '会议信息',
    guests: '嘉宾管理',
    fields: '嘉宾字段',
    assistant: '会议服务',
    staff: '工作人员',
    checkins: '签到管理',
  }
  return titleMap[resolveActiveSection()] || '数据总览'
}

/**
 * 计算当前会议已签到人数所占的百分比。
 *
 * 入参：无；函数读取嘉宾总数和签到记录数。
 * 返回值：number：范围为 0 到 100 的整数百分比；没有嘉宾时返回 0。
 * 异常：当前函数不主动抛出异常。
 */
function resolveCheckInRate(): number {
  if (!totalGuestCount.value) {
    return 0
  }
  return Math.min(100, Math.round((checkedCount.value / totalGuestCount.value) * 100))
}

/**
 * 根据现有签到场次推断默认展示的签到模式。
 *
 * 入参：sessions 为当前会议的签到场次列表，必填。
 * 返回值：CheckInMode：存在日期场次时返回 date，多场非日期返回 custom，否则返回 single。
 * 异常：当前函数不主动抛出异常。
 */
function inferCheckInMode(sessions: CheckInSession[]): CheckInMode {
  if (sessions.some(isFullDayDateSession)) {
    return 'date'
  }
  if (sessions.length > 1) {
    return 'custom'
  }
  return 'single'
}

/**
 * 读取当前签到规则的展示信息。
 *
 * 入参：无；函数读取当前签到规则和手动覆盖状态。
 * 返回值：{ label: string; description: string }：用于规则栏展示的标题和说明。
 * 异常：当前函数不主动抛出异常。
 */
function resolveCheckInModeMeta(): { label: string; description: string } {
  if (checkInMode.value === 'date') {
    return {
      label: checkInManualDefaultSessionId.value ? '日期场次 · 手动覆盖' : '日期场次 · 自动切换',
      description: checkInManualDefaultSessionId.value
        ? '当前由管理员手动指定默认场次，可恢复为按系统日期自动切换。'
        : '系统按服务端当前日期自动选择当天签到场次。',
    }
  }
  if (checkInMode.value === 'custom') {
    return {
      label: '自定义场次',
      description: '管理员手动维护场次顺序和当前默认签到场次。',
    }
  }
  return {
    label: '单场签到',
    description: '整场会议只使用一个默认签到场次。',
  }
}

/**
 * 读取当前签到模式与场次数量之间的业务提示。
 *
 * 入参：无；函数读取当前签到模式、会议日期和已加载场次。
 * 返回值：string：用于签到场次卡片副标题的简短业务规则说明。
 * 异常：当前函数不主动抛出异常；会议日期不完整时回退为通用提示。
 */
function resolveCheckInModeCountHint(): string {
  if (checkInMode.value === 'single') {
    return `单场签到建议保留 1 个有效场次，当前 ${checkInSessions.value.length} 个。`
  }
  if (checkInMode.value === 'date') {
    const summary = dateSessionGenerationSummary.value
    if (!summary.total) {
      return '按日期签到需要会议开始和结束日期完整后生成日期场次。'
    }
    return `按日期签到建议与会议自然日一致：会议共 ${summary.total} 天，已生成 ${summary.existing}/${summary.total} 天。`
  }
  return `自定义场次允许 1 个或多个，当前 ${checkInSessions.value.length} 个，由管理员按流程维护。`
}

/**
 * 按关键词过滤签到场次列表。
 *
 * 入参：无；函数读取场次列表和搜索关键词。
 * 返回值：CheckInSession[]：匹配关键词的场次列表。
 * 异常：当前函数不主动抛出异常。
 */
function filterCheckInSessions(): CheckInSession[] {
  const keyword = checkInSessionKeyword.value.trim().toLowerCase()
  if (!keyword) {
    return checkInSessions.value
  }
  return checkInSessions.value.filter((sessionItem) => {
    return [sessionItem.title, sessionItem.description, sessionTypeText(sessionItem)]
      .join(' ')
      .toLowerCase()
      .includes(keyword)
  })
}

/**
 * 统计会议日期场次的生成状态。
 *
 * 入参：无；函数读取当前会议和已加载的签到场次列表。
 * 返回值：DateSessionGenerationSummary：包含会议天数、已存在天数、缺失天数、按钮文案和是否禁用。
 * 异常：当前函数不主动抛出异常；会议日期不可用时返回禁用状态。
 */
function resolveDateSessionGenerationSummary(): DateSessionGenerationSummary {
  if (!meeting.value) {
    return { total: 0, existing: 0, missing: 0, label: '生成日期场次', disabled: true }
  }
  const dateKeys = meetingDateKeys(meeting.value)
  if (!dateKeys.length) {
    return { total: 0, existing: 0, missing: 0, label: '会议日期不完整', disabled: true }
  }
  const existingTitles = new Set(checkInSessions.value.map((item) => item.title))
  const existing = dateKeys.filter((item) => existingTitles.has(item.title)).length
  const missing = Math.max(dateKeys.length - existing, 0)
  if (!missing) {
    return { total: dateKeys.length, existing, missing, label: `已生成 ${existing}/${dateKeys.length} 天`, disabled: true }
  }
  const label = existing ? `补齐缺失日期场次 ${existing}/${dateKeys.length}` : '生成日期场次'
  return { total: dateKeys.length, existing, missing, label, disabled: false }
}

/**
 * 计算当前选中签到场次的签到率。
 *
 * 入参：无；函数读取嘉宾总数和当前场次签到记录数。
 * 返回值：number：范围为 0 到 100 的整数百分比。
 * 异常：当前函数不主动抛出异常。
 */
function resolveSelectedSessionRate(): number {
  if (!totalGuestCount.value) {
    return 0
  }
  return Math.min(100, Math.round((checkIns.value.length / totalGuestCount.value) * 100))
}

/**
 * 判断签到场次是否为当前选中的统计场次。
 *
 * 入参：sessionItem 为签到场次，必填。
 * 返回值：boolean：场次 ID 与当前统计场次一致时返回 true。
 * 异常：当前函数不主动抛出异常。
 */
function isSelectedCheckInSession(sessionItem: CheckInSession): boolean {
  return sessionItem.id === selectedCheckInSessionId.value
}

/**
 * 读取场次行的已签到人数。
 *
 * 入参：sessionItem 为签到场次，必填。
 * 返回值：number | string：当前选中场次返回真实人数，其他场次返回横线。
 * 异常：当前函数不主动抛出异常。
 */
function sessionRecordCount(sessionItem: CheckInSession): number | string {
  return isSelectedCheckInSession(sessionItem) ? checkIns.value.length : '—'
}

/**
 * 读取场次行的待签到人数。
 *
 * 入参：sessionItem 为签到场次，必填。
 * 返回值：number | string：当前选中场次返回真实人数，其他场次返回横线。
 * 异常：当前函数不主动抛出异常。
 */
function sessionUncheckedCount(sessionItem: CheckInSession): number | string {
  return isSelectedCheckInSession(sessionItem) ? Math.max(totalGuestCount.value - checkIns.value.length, 0) : '—'
}

/**
 * 计算场次状态列表中的签到进度。
 *
 * 入参：sessionItem 为签到场次，必填。
 * 返回值：number：当前选中场次返回 0 到 100 的签到率，其他场次因未加载明细返回 0。
 * 异常：当前函数不主动抛出异常。
 */
function sessionProgressPercentage(sessionItem: CheckInSession): number {
  if (!isSelectedCheckInSession(sessionItem) || !totalGuestCount.value) {
    return 0
  }
  return Math.min(100, Math.round((checkIns.value.length / totalGuestCount.value) * 100))
}

/**
 * 读取场次状态列表中的进度文案。
 *
 * 入参：sessionItem 为签到场次，必填。
 * 返回值：string：当前选中场次返回百分比，其他场次返回横线。
 * 异常：当前函数不主动抛出异常。
 */
function sessionProgressText(sessionItem: CheckInSession): string {
  return isSelectedCheckInSession(sessionItem) ? `${sessionProgressPercentage(sessionItem)}%` : '—'
}

/**
 * 解析提供给嘉宾访问的前端公开地址。
 *
 * 入参：无；优先读取 `VITE_PUBLIC_APP_URL`，未配置时读取管理员当前访问页面的来源地址。
 * 返回值：string：去除末尾斜杠后的本机 IP 或域名地址；通过 localhost 访问且未配置公开地址时返回空字符串。
 * 异常：当前函数不主动抛出异常；配置为空或不可用于外部访问时返回空字符串。
 * 使用示例：配置 `VITE_PUBLIC_APP_URL=https://meeting.example.com` 后返回 `https://meeting.example.com`。
 */
function resolvePublicAppBaseUrl(): string {
  const configuredUrl = import.meta.env.VITE_PUBLIC_APP_URL?.trim().replace(/\/+$/, '')
  if (configuredUrl) {
    return configuredUrl
  }

  const localHostNames = new Set(['localhost', '127.0.0.1', '::1'])
  return localHostNames.has(window.location.hostname) ? '' : window.location.origin
}

/**
 * 加载管理员会议详情页所需数据。
 *
 * 入参：无。
 *
 * 返回值：Promise<void>：加载完成后更新会议、嘉宾、字段、工作人员、签到记录和会议助手配置。
 *
 * 异常：会议身份、权限或网络异常时清空详情并展示后端错误；独立资源失败时展示各自错误状态。
 */
async function loadDetail(): Promise<void> {
  if (!session.admin) {
    detailLoading.value = false
    detailError.value = '请先完成管理员登录。'
    return
  }
  const meetingId = String(route.params.id)
  detailLoading.value = true
  detailError.value = ''
  try {
    const [meetingData, guestData, fieldData, displayFieldData, registrationSettings, staffData] = await Promise.all([
      getAdminMeeting(meetingId),
      listAdminGuests(meetingId),
      listAdminGuestFields(meetingId),
      getAdminGuestDisplayFields(meetingId),
      getAdminGuestRegistrationSettings(meetingId),
      listAdminStaff(meetingId),
    ])
    meeting.value = meetingData
    guests.value = guestData
    fields.value = fieldData
    savedVisibleGuestFieldKeys.value = displayFieldData
    savedGuestRegistrationSettings.value = registrationSettings
    resetGuestFieldDrafts(fieldData, displayFieldData, registrationSettings)
    staff.value = staffData
    totalGuestCount.value = guestData.length
    resetEditForm()
  } catch (error) {
    meeting.value = undefined
    detailError.value = getApiErrorMessage(error, '会议详情加载失败。')
  } finally {
    detailLoading.value = false
  }
  if (meeting.value) {
    await Promise.all([loadAssistantFeatures(meetingId), loadCheckInState(meetingId), loadGuestApplications(meetingId)])
  }
}

/**
 * 独立加载会议助手配置，失败时保留会议其他资料。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<void>：成功后更新五项配置，失败后展示独立错误。
 * 异常：接口异常在函数内转换为页面错误提示。
 */
async function loadAssistantFeatures(meetingId: string): Promise<void> {
  assistantLoading.value = true
  assistantError.value = ''
  try {
    assistantFeatures.value = await listAdminMeetingAssistantFeatures(meetingId)
  } catch (error) {
    assistantFeatures.value = []
    assistantError.value = getApiErrorMessage(error, '会议助手配置加载失败。')
  } finally {
    assistantLoading.value = false
  }
}

/**
 * 独立加载会议签到场次列表。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<void>：成功后更新场次列表和当前选中场次。
 * 异常：接口异常在函数内转换为签到页签错误，不影响会议其他资料。
 */
async function loadCheckInSessions(meetingId: string): Promise<void> {
  checkInSessionLoading.value = true
  checkInError.value = ''
  try {
    const [settings, sessions] = await Promise.all([
      getAdminCheckInSettings(meetingId),
      listAdminCheckInSessions(meetingId),
    ])
    checkInSessions.value = sessions
    checkInMode.value = settings.mode || inferCheckInMode(sessions)
    checkInManualDefaultSessionId.value = settings.manualDefaultSessionId || ''
    const effectiveSession = sessions.find((item) => item.id === settings.effectiveSessionId)
    const defaultSession = sessions.find((item) => item.isDefault)
    const existingSession = checkInSessions.value.find((item) => item.id === selectedCheckInSessionId.value)
    selectedCheckInSessionId.value = existingSession?.id || effectiveSession?.id || defaultSession?.id || sessions[0]?.id || ''
  } catch (error) {
    checkInSessions.value = []
    selectedCheckInSessionId.value = ''
    checkInManualDefaultSessionId.value = ''
    checkInError.value = getApiErrorMessage(error, '签到场次加载失败。')
  } finally {
    checkInSessionLoading.value = false
  }
}

/**
 * 加载会议签到场次及当前场次统计。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<void>：成功后更新场次、统计、记录和场次差异。
 * 异常：场次或统计接口异常会转换为签到页签错误。
 */
async function loadCheckInState(meetingId: string): Promise<void> {
  await loadCheckInSessions(meetingId)
  if (selectedCheckInSessionId.value) {
    await loadCheckInSummary(meetingId, selectedCheckInSessionId.value)
  }
}

/**
 * 独立加载管理员签到统计和明细。
 *
 * 入参：meetingId 为会议 ID；sessionId 为可选签到场次 ID。
 * 返回值：Promise<void>：成功后更新总数、签到记录和嘉宾签到状态。
 * 异常：接口异常在函数内转换为签到页签错误，不影响会议其他资料。
 */
async function loadCheckInSummary(meetingId: string, sessionId?: string): Promise<void> {
  checkInLoading.value = true
  checkInError.value = ''
  try {
    const summary = await getAdminCheckInSummary(meetingId, sessionId)
    selectedCheckInSessionId.value = summary.sessionId
    totalGuestCount.value = summary.totalGuests
    checkIns.value = summary.records
    checkInComparison.value = summary.comparison
  } catch (error) {
    checkIns.value = []
    checkInComparison.value = undefined
    checkInError.value = getApiErrorMessage(error, '签到统计加载失败。')
  } finally {
    checkInLoading.value = false
  }
}

/**
 * 创建空白签到场次表单状态。
 *
 * 入参：无。
 * 返回值：CheckInSessionFormState：可直接绑定到新增场次表单的空状态。
 * 异常：当前函数不主动抛出异常。
 */
function createEmptyCheckInSessionForm(): CheckInSessionFormState {
  return {
    id: '',
    title: '',
    description: '',
    startsAt: '',
    endsAt: '',
    isDefault: false,
  }
}

/**
 * 清空签到场次编辑表单。
 *
 * 入参：无。
 * 返回值：void：恢复新增模式。
 * 异常：当前函数不主动抛出异常。
 */
function resetCheckInSessionForm(): void {
  checkInSessionForm.value = createEmptyCheckInSessionForm()
}

/**
 * 关闭签到场次编辑弹窗。
 *
 * 入参：无。
 * 返回值：void：关闭弹窗，表单会在关闭动画结束后自动重置。
 * 异常：当前函数不主动抛出异常。
 */
function closeCheckInSessionDialog(): void {
  checkInSessionDialogVisible.value = false
}

/**
 * 进入新增自定义场次模式。
 *
 * 入参：无。
 * 返回值：void：切换为自定义模式，清空场次表单并打开编辑弹窗。
 * 异常：当前函数不主动抛出异常。
 */
function prepareCustomCheckInSession(): void {
  checkInMode.value = 'custom'
  resetCheckInSessionForm()
  checkInSessionDialogVisible.value = true
}

/**
 * 将签到场次填充到编辑表单。
 *
 * 入参：sessionItem 为管理员选中的签到场次，必填。
 * 返回值：void：打开编辑弹窗并保留当前签到记录选中场次。
 * 异常：当前函数不主动抛出异常。
 */
function editCheckInSession(sessionItem: CheckInSession): void {
  checkInSessionForm.value = {
    id: sessionItem.id,
    title: sessionItem.title,
    description: sessionItem.description,
    startsAt: sessionItem.startsAt ? toDateTimeLocalValue(sessionItem.startsAt) : '',
    endsAt: sessionItem.endsAt ? toDateTimeLocalValue(sessionItem.endsAt) : '',
    isDefault: sessionItem.isDefault,
  }
  checkInSessionDialogVisible.value = true
}

/**
 * 保存新增或编辑的签到场次。
 *
 * 入参：无；函数读取当前会议和场次表单。
 * 返回值：Promise<void>：保存成功后刷新场次列表与当前统计。
 * 异常：名称为空、时间无效、权限或网络异常时展示错误提示。
 */
async function saveCheckInSession(): Promise<void> {
  if (!meeting.value) {
    return
  }
  if (!checkInSessionForm.value.title.trim()) {
    ElMessage.warning('请填写签到场次名称。')
    return
  }
  const payload = {
    title: checkInSessionForm.value.title.trim(),
    description: checkInSessionForm.value.description.trim(),
    startsAt: toIsoWithChinaTimezone(checkInSessionForm.value.startsAt),
    endsAt: toIsoWithChinaTimezone(checkInSessionForm.value.endsAt),
    isDefault: checkInSessionForm.value.isDefault,
  }
  savingCheckInSession.value = true
  try {
    const savedSession = checkInSessionForm.value.id
      ? await updateAdminCheckInSession(meeting.value.id, checkInSessionForm.value.id, payload)
      : await createAdminCheckInSession(meeting.value.id, payload)
    if (!checkInSessionForm.value.id) {
      await updateAdminCheckInSettings(meeting.value.id, {
        mode: 'custom',
        manualDefaultSessionId: null,
      })
    }
    selectedCheckInSessionId.value = savedSession.id
    closeCheckInSessionDialog()
    await loadCheckInState(meeting.value.id)
    ElMessage.success('签到场次已保存。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '签到场次保存失败。'))
  } finally {
    savingCheckInSession.value = false
  }
}

/**
 * 将指定签到场次设置为默认场次。
 *
 * 入参：sessionItem 为要设置为默认的签到场次，必填。
 * 返回值：Promise<void>：保存成功后刷新场次列表和当前统计。
 * 异常：权限、网络或业务异常时展示错误提示。
 */
async function setDefaultCheckInSession(sessionItem: CheckInSession): Promise<void> {
  if (!meeting.value || sessionItem.isDefault) {
    return
  }
  savingCheckInSession.value = true
  try {
    const savedSession = await updateAdminCheckInSession(meeting.value.id, sessionItem.id, {
      title: sessionItem.title,
      description: sessionItem.description,
      startsAt: sessionItem.startsAt,
      endsAt: sessionItem.endsAt,
      isDefault: true,
    })
    await updateAdminCheckInSettings(meeting.value.id, {
      mode: checkInMode.value === 'date' ? 'date' : 'custom',
      manualDefaultSessionId: checkInMode.value === 'date' ? savedSession.id : null,
    })
    selectedCheckInSessionId.value = savedSession.id
    await loadCheckInState(meeting.value.id)
    ElMessage.success('默认签到场次已切换。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '默认场次切换失败。'))
  } finally {
    savingCheckInSession.value = false
  }
}

/**
 * 二次确认并删除签到场次。
 *
 * 入参：sessionItem 为待删除签到场次，必填。
 * 返回值：Promise<void>：确认删除后刷新场次列表和当前统计。
 * 异常：用户取消时静默返回；权限、网络或业务异常时展示错误提示。
 */
async function confirmDeleteCheckInSession(sessionItem: CheckInSession): Promise<void> {
  if (!meeting.value) {
    return
  }
  try {
    await ElMessageBox.confirm(
      sessionItem.isDefault
        ? `确定删除“${sessionItem.title}”吗？该场次是当前默认场次，删除后系统会自动切换剩余场次为默认。`
        : `确定删除“${sessionItem.title}”吗？该场次下已有签到记录也会一并删除。`,
      '删除签到场次',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
  } catch {
    return
  }
  deletingCheckInSessionId.value = sessionItem.id
  try {
    await deleteAdminCheckInSession(meeting.value.id, sessionItem.id)
    if (selectedCheckInSessionId.value === sessionItem.id) {
      selectedCheckInSessionId.value = ''
    }
    await loadCheckInState(meeting.value.id)
    ElMessage.success('签到场次已删除。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '签到场次删除失败。'))
  } finally {
    deletingCheckInSessionId.value = ''
  }
}

/**
 * 根据会议日期生成每日签到场次。
 *
 * 入参：无；函数读取当前会议开始和结束日期。
 * 返回值：Promise<void>：成功后创建缺失的日期场次并刷新场次列表。
 * 异常：会议日期缺失、日期无效、权限或网络异常时展示错误提示。
 */
async function generateDateCheckInSessions(): Promise<void> {
  if (!meeting.value) {
    return
  }
  const dateKeys = meetingDateKeys(meeting.value)
  if (!dateKeys.length) {
    ElMessage.warning('会议开始和结束日期不完整，无法生成日期场次。')
    return
  }
  const existingTitles = new Set(checkInSessions.value.map((item) => item.title))
  const missingDates = dateKeys.filter((item) => !existingTitles.has(item.title))
  if (!missingDates.length) {
    try {
      await updateAdminCheckInSettings(meeting.value.id, {
        mode: 'date',
        manualDefaultSessionId: null,
      })
      await loadCheckInState(meeting.value.id)
      ElMessage.success('已恢复按日期自动切换。')
    } catch (error) {
      ElMessage.error(getApiErrorMessage(error, '日期场次规则保存失败。'))
    }
    return
  }
  generatingDateSessions.value = true
  try {
    for (const item of missingDates) {
      await createAdminCheckInSession(meeting.value.id, {
        title: item.title,
        description: '系统按会议日期生成的签到场次。',
        startsAt: `${item.dateKey}T00:00:00+08:00`,
        endsAt: `${item.dateKey}T23:59:00+08:00`,
        isDefault: item.dateKey === todayChinaDateKey(),
      })
    }
    await updateAdminCheckInSettings(meeting.value.id, {
      mode: 'date',
      manualDefaultSessionId: null,
    })
    await loadCheckInState(meeting.value.id)
    ElMessage.success(`已生成 ${missingDates.length} 个日期签到场次。`)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '日期场次生成失败。'))
  } finally {
    generatingDateSessions.value = false
  }
}

/**
 * 恢复日期场次按系统日期自动选择默认场次。
 *
 * 入参：无；函数读取当前会议 ID。
 * 返回值：Promise<void>：保存成功后刷新场次和统计。
 * 异常：权限、网络或规则保存失败时展示错误提示。
 */
async function restoreDateAutoDefault(): Promise<void> {
  if (!meeting.value) {
    return
  }
  savingCheckInSession.value = true
  try {
    await updateAdminCheckInSettings(meeting.value.id, {
      mode: 'date',
      manualDefaultSessionId: null,
    })
    await loadCheckInState(meeting.value.id)
    ElMessage.success('已恢复按日期自动切换。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '恢复自动切换失败。'))
  } finally {
    savingCheckInSession.value = false
  }
}

/**
 * 响应管理员切换签到场次并刷新统计。
 *
 * 入参：sessionId 为选中的签到场次 ID，必填。
 * 返回值：void：存在会议时异步刷新当前场次记录。
 * 异常：接口异常由 `loadCheckInSummary` 转换为页面错误提示。
 */
function handleCheckInSessionSelect(sessionId: string): void {
  if (!meeting.value || !sessionId) {
    return
  }
  void loadCheckInSummary(meeting.value.id, sessionId)
}

/**
 * 打开签到明细弹窗。
 *
 * 入参：无；函数读取当前选中的签到场次和已加载签到记录。
 * 返回值：void：显示签到明细弹窗。
 * 异常：当前函数不主动抛出异常。
 */
function openCheckInRecordDialog(): void {
  checkInRecordDialogVisible.value = true
}

/**
 * 将签到场次时间范围转换为后台列表文案。
 *
 * 入参：sessionItem 为签到场次，必填。
 * 返回值：string：完整时间范围、单侧时间或“未设置时间”。
 * 异常：当前函数不主动抛出异常。
 */
function sessionTimeText(sessionItem: CheckInSession): string {
  if (sessionItem.startsAt && sessionItem.endsAt) {
    return `${formatDate(sessionItem.startsAt)} - ${formatDate(sessionItem.endsAt)}`
  }
  if (sessionItem.startsAt) {
    return `${formatDate(sessionItem.startsAt)}开始`
  }
  if (sessionItem.endsAt) {
    return `${formatDate(sessionItem.endsAt)}结束`
  }
  return '未设置时间'
}

/**
 * 识别签到场次类型展示文案。
 *
 * 入参：sessionItem 为签到场次，必填。
 * 返回值：string：单场、日期场次或自定义场次。
 * 异常：当前函数不主动抛出异常。
 */
function sessionTypeText(sessionItem: CheckInSession): string {
  if (checkInSessions.value.length === 1 && sessionItem.isDefault) {
    return '单场'
  }
  if (isFullDayDateSession(sessionItem)) {
    return '日期场次'
  }
  return '自定义'
}

/**
 * 判断场次是否像系统生成的整日日期场次。
 *
 * 入参：sessionItem 为签到场次，必填。
 * 返回值：boolean：开始和结束时间位于同一天且覆盖整日时返回 true。
 * 异常：当前函数不主动抛出异常。
 */
function isFullDayDateSession(sessionItem: CheckInSession): boolean {
  if (!sessionItem.startsAt || !sessionItem.endsAt) {
    return false
  }
  const startsAt = toDateTimeLocalValue(sessionItem.startsAt)
  const endsAt = toDateTimeLocalValue(sessionItem.endsAt)
  return startsAt.slice(0, 10) === endsAt.slice(0, 10)
    && startsAt.endsWith('00:00')
    && (endsAt.endsWith('23:59') || endsAt.endsWith('23:59:00'))
}

/**
 * 生成会议覆盖的中国日期键列表。
 *
 * 入参：sourceMeeting 为当前会议，必填。
 * 返回值：Array<{ dateKey: string; title: string }>：每日日期键和默认场次标题。
 * 异常：当前函数不主动抛出异常；日期无效时返回空数组。
 */
function meetingDateKeys(sourceMeeting: Meeting): Array<{ dateKey: string; title: string }> {
  const startDateKey = toChinaDateKey(sourceMeeting.startTime)
  const endDateKey = toChinaDateKey(sourceMeeting.endTime)
  if (!startDateKey || !endDateKey || startDateKey > endDateKey) {
    return []
  }
  const result: Array<{ dateKey: string; title: string }> = []
  const cursor = new Date(`${startDateKey}T00:00:00+08:00`)
  const endDate = new Date(`${endDateKey}T00:00:00+08:00`)
  while (cursor <= endDate) {
    const dateKey = toChinaDateKey(cursor.toISOString())
    if (!dateKey) {
      break
    }
    result.push({ dateKey, title: `${dayIndexText(result.length + 1)}签到` })
    cursor.setUTCDate(cursor.getUTCDate() + 1)
  }
  return result
}

/**
 * 将日期时间转换为中国日期键。
 *
 * 入参：value 为 ISO 日期字符串，必填。
 * 返回值：string：形如 yyyy-MM-dd 的日期键；无效日期返回空字符串。
 * 异常：当前函数不主动抛出异常。
 */
function toChinaDateKey(value: string): string {
  if (!value) {
    return ''
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
  return formatter.format(date)
}

/**
 * 读取今天的中国日期键。
 *
 * 入参：无。
 * 返回值：string：形如 yyyy-MM-dd 的当天日期。
 * 异常：当前函数不主动抛出异常。
 */
function todayChinaDateKey(): string {
  return toChinaDateKey(new Date().toISOString())
}

/**
 * 将日期序号转换为中文场次标题前缀。
 *
 * 入参：index 为从 1 开始的日期序号，必填。
 * 返回值：string：第一天、第二天等标题前缀。
 * 异常：当前函数不主动抛出异常。
 */
function dayIndexText(index: number): string {
  const textMap = ['第一天', '第二天', '第三天', '第四天', '第五天', '第六天', '第七天']
  return textMap[index - 1] || `第${index}天`
}

/**
 * 同步刷新嘉宾列表与签到统计，保证详情页不同区域使用同一份最新人数状态。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<void>：嘉宾列表与签到统计请求结束后更新页面状态。
 * 异常：嘉宾列表加载失败时向调用方抛出；签到统计失败时由 `loadCheckInSummary` 转换为页面错误提示。
 * 使用示例：新增或导入嘉宾成功后调用 `await refreshGuestAndCheckInState(meetingId)`。
 */
async function refreshGuestAndCheckInState(meetingId: string): Promise<void> {
  const [guestData] = await Promise.all([
    listAdminGuests(meetingId),
    loadCheckInSummary(meetingId, selectedCheckInSessionId.value || undefined),
  ])
  guests.value = guestData
}

/**
 * 使用已保存字段重建管理员字段编辑草稿。
 *
 * 入参：sourceFields 为后端返回的会议动态字段列表；visibleFieldKeys 为已保存的呈现字段 key，均必填。
 * 返回值：void：按原顺序更新固定和扩展字段编辑草稿，并清除字段操作提示。
 * 异常：当前函数不主动抛出异常。
 */
function resetGuestFieldDrafts(
  sourceFields: GuestField[],
  visibleFieldKeys: string[],
  registrationSettings: AdminGuestRegistrationSettings,
): void {
  const visibleFieldSet = new Set(visibleFieldKeys)
  const registrationFieldSet = new Set(registrationSettings.fields)
  const requiredFieldSet = new Set(registrationSettings.requiredFields)
  const enabledFieldSet = new Set(registrationSettings.enabledFields)
  fixedGuestFieldDrafts.value = fixedGuestFieldDrafts.value.map((field) => ({
    ...field,
    visibleToGuest: visibleFieldSet.has(field.key),
    registrationVisible: registrationFieldSet.has(field.key),
    required: requiredFieldSet.has(field.key),
    isEnabled: enabledFieldSet.has(field.key),
  }))
  guestFieldDrafts.value = sourceFields.map((field) => ({
    clientId: field.id,
    label: field.label,
    key: field.key,
    type: field.type,
    required: field.required,
    visibleToGuest: field.visibleToGuest,
    isEnabled: field.isEnabled,
    profileVisible: visibleFieldSet.has(field.key),
  }))
  guestFieldMessage.value = ''
}

/**
 * 按固定字段与扩展字段的页面顺序汇总当前选中的嘉宾端呈现字段。
 *
 * 入参：无；函数读取固定字段和扩展字段编辑草稿。
 * 返回值：string[]：已启用呈现的字段 key，固定字段排列在扩展字段之前。
 * 异常：当前函数不主动抛出异常；未填写 key 的新增草稿不会进入返回值。
 */
function selectedGuestDisplayFieldKeys(): string[] {
  return [
    ...fixedGuestFieldDrafts.value.filter((field) => field.visibleToGuest && field.isEnabled).map((field) => field.key),
    ...guestFieldDrafts.value
      .filter((field) => field.profileVisible && field.isEnabled && field.key.trim())
      .map((field) => field.key.trim()),
  ]
}

/**
 * 汇总固定嘉宾字段在公开报名页中的当前配置。
 *
 * 入参：无；函数读取固定字段编辑草稿。
 * 返回值：AdminGuestRegistrationSettings：报名表单、必填和启用字段 key 列表。
 * 异常：当前函数不主动抛出异常；姓名和手机号由后端再次强制保护。
 */
function currentFixedGuestRegistrationSettings(): AdminGuestRegistrationSettings {
  return {
    fields: fixedGuestFieldDrafts.value
      .filter((field) => field.registrationVisible && field.isEnabled)
      .map((field) => field.key),
    requiredFields: fixedGuestFieldDrafts.value
      .filter((field) => field.required && field.registrationVisible && field.isEnabled)
      .map((field) => field.key),
    enabledFields: fixedGuestFieldDrafts.value
      .filter((field) => field.isEnabled)
      .map((field) => field.key),
  }
}

/**
 * 加载当前会议的自主报名申请，用于嘉宾管理页审核。
 *
 * 入参：meetingId 为会议 ID，必填。
 * 返回值：Promise<void>：成功后更新申请列表；失败时仅设置独立错误提示。
 * 异常：接口异常在函数内转换为页面提示，不影响正式嘉宾列表。
 */
async function loadGuestApplications(meetingId: string): Promise<void> {
  guestApplicationError.value = ''
  try {
    guestApplications.value = await listAdminGuestApplications(meetingId)
  } catch (error) {
    guestApplications.value = []
    guestApplicationError.value = getApiErrorMessage(error, '自主报名申请加载失败。')
  }
}

/**
 * 审核一条嘉宾自主报名申请，并在通过后刷新正式嘉宾与签到统计。
 *
 * 入参：application 为待审核申请；status 为通过或拒绝结果，均必填。
 * 返回值：Promise<void>：审核完成后刷新申请和嘉宾列表。
 * 异常：申请已处理、字段不完整、权限或网络异常时展示消息提示。
 */
async function reviewGuestApplication(
  application: AdminGuestApplication,
  status: 'approved' | 'rejected',
): Promise<void> {
  if (!meeting.value) {
    return
  }
  reviewingApplicationId.value = application.id
  try {
    await reviewAdminGuestApplication(meeting.value.id, application.id, status)
    await Promise.all([loadGuestApplications(meeting.value.id), refreshGuestAndCheckInState(meeting.value.id)])
    ElMessage.success(status === 'approved' ? '报名已通过，嘉宾二维码已生成。' : '报名申请已拒绝。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '报名审核失败。'))
  } finally {
    reviewingApplicationId.value = ''
  }
}

/**
 * 将后端嘉宾来源编码转换为后台表格中的中文文字。
 *
 * 入参：source 为嘉宾来源编码，可为空。
 * 返回值：string：自主报名、后台导入或后台录入的可读文字。
 * 异常：当前函数不主动抛出异常；未知来源回退为“后台录入”。
 */
function guestSourceText(source?: Guest['source']): string {
  if (source === 'self_registration') {
    return '自主报名'
  }
  if (source === 'admin_import') {
    return '后台导入'
  }
  return '后台录入'
}

/**
 * 将正式嘉宾与尚未转化为嘉宾的自主报名申请组合为统一列表行。
 *
 * 入参：无；函数读取嘉宾、报名申请和签到记录。
 * 返回值：GuestManagementRow[]：正式嘉宾与待审核、已拒绝报名申请组成的管理列表。
 * 异常：当前函数不主动抛出异常。
 */
function resolveGuestManagementRows(): GuestManagementRow[] {
  const guestEntries = guestRows.value.map((guest) => ({
    id: `guest-${guest.id}`,
    recordType: 'guest' as const,
    name: guest.name,
    phone: guest.phone,
    organization: guest.organization,
    title: guest.title,
    source: guest.source,
    status: guest.source === 'self_registration' ? 'approved' as const : 'entered' as const,
    checkedIn: guest.checkedIn,
    guest,
  }))
  const applicationEntries = guestApplications.value
    .filter((application) => application.status !== 'approved')
    .map((application) => ({
      id: `application-${application.id}`,
      recordType: 'application' as const,
      name: application.name,
      phone: application.phone,
      organization: application.organization,
      title: application.title,
      source: 'self_registration' as const,
      status: application.status,
      checkedIn: false,
      application,
    }))
  return [...applicationEntries, ...guestEntries]
}

/**
 * 按页面筛选条件过滤统一嘉宾管理列表。
 *
 * 入参：无；函数读取状态、签到和关键字筛选条件。
 * 返回值：GuestManagementRow[]：满足全部条件的列表行。
 * 异常：当前函数不主动抛出异常；空搜索条件表示不限制关键字。
 */
function filterGuestManagementRows(): GuestManagementRow[] {
  const keyword = guestSearchKeyword.value.trim().toLowerCase()
  return guestManagementRows.value.filter((row) => {
    if (guestStatusFilter.value !== 'all' && row.status !== guestStatusFilter.value) {
      return false
    }
    if (guestCheckInFilter.value === 'checked' && !row.checkedIn) {
      return false
    }
    if (guestCheckInFilter.value === 'unchecked' && row.checkedIn) {
      return false
    }
    if (!keyword) {
      return true
    }
    return [row.name, row.phone, row.organization, row.title, guestSourceText(row.source)]
      .join(' ')
      .toLowerCase()
      .includes(keyword)
  })
}

/**
 * 将统一列表的审核状态转换为中文文字。
 *
 * 入参：status 为管理行状态，必填。
 * 返回值：string：适合状态标签呈现的中文文字。
 * 异常：当前函数不主动抛出异常。
 */
function guestManagementStatusText(status: GuestManagementRow['status']): string {
  const statusMap: Record<GuestManagementRow['status'], string> = {
    pending: '待审核',
    approved: '已通过',
    entered: '已录入',
    rejected: '已拒绝',
  }
  return statusMap[status]
}

/**
 * 将统一列表的审核状态转换为主题一致的 Element Plus 标签类型。
 *
 * 入参：status 为管理行状态，必填。
 * 返回值：'success' | 'warning' | 'info' | 'danger'：状态标签视觉类型。
 * 异常：当前函数不主动抛出异常。
 */
function guestManagementStatusTagType(
  status: GuestManagementRow['status'],
): 'success' | 'warning' | 'info' | 'danger' {
  if (status === 'approved') {
    return 'success'
  }
  if (status === 'pending') {
    return 'warning'
  }
  if (status === 'rejected') {
    return 'danger'
  }
  return 'info'
}

/**
 * 为新增扩展字段生成页面不可见的稳定唯一标识。
 *
 * 入参：无；函数读取当前已保存字段和字段草稿中的 key。
 * 返回值：string：以 `custom_` 开头、满足后端格式约束且在当前会议内不重复的字段 key。
 * 异常：当前函数不主动抛出异常；同一毫秒连续新增时通过递增后缀消除冲突。
 * 使用示例：新增字段时可能返回 `custom_1784567890123`。
 */
function createGuestFieldKey(): string {
  const existingKeys = new Set([
    ...fields.value.map((field) => field.key),
    ...guestFieldDrafts.value.map((field) => field.key).filter(Boolean),
  ])
  const timestamp = Date.now()
  let suffix = 0
  let candidate = `custom_${timestamp}`
  // 极短时间内连续新增字段时递增后缀，确保稳定标识不会重复。
  while (existingKeys.has(candidate)) {
    suffix += 1
    candidate = `custom_${timestamp}_${suffix}`
  }
  return candidate
}

/**
 * 在字段编辑表格末尾增加一个空白文本字段。
 *
 * 入参：无。
 * 返回值：void：新增一行带稳定页面标识的字段草稿。
 * 异常：当前函数不主动抛出异常。
 */
function addGuestFieldDraft(): void {
  const fieldKey = createGuestFieldKey()
  guestFieldDrafts.value.push({
    clientId: `new-${fieldKey}`,
    label: '',
    key: fieldKey,
    type: 'text',
    required: false,
    visibleToGuest: true,
    isEnabled: true,
    profileVisible: true,
  })
  guestFieldMessage.value = ''
}

/**
 * 删除指定位置的字段编辑草稿。
 *
 * 入参：index 为字段草稿数组下标，必须处于当前数组范围内。
 * 返回值：void：移除对应字段草稿；下标无效时保持原状态。
 * 异常：当前函数不主动抛出异常。
 */
function removeGuestFieldDraft(index: number): void {
  if (index < 0 || index >= guestFieldDrafts.value.length) {
    return
  }
  guestFieldDrafts.value.splice(index, 1)
  guestFieldMessage.value = ''
}

/**
 * 校验并增量保存当前会议的动态嘉宾字段。
 *
 * 入参：无；读取当前会议与字段编辑草稿。
 * 返回值：Promise<void>：保存成功后以服务端返回结果刷新字段定义和嘉宾端呈现选择。
 * 异常：名称为空、字段标识格式错误或重复时展示本地提示；删除含值字段、修改含值字段类型、权限或网络异常时展示后端错误。
 * 使用示例：新增“饮食偏好 / diet_preference”后点击“保存字段”。
 */
async function saveGuestFields(): Promise<void> {
  if (!meeting.value) {
    return
  }
  // 兼容热更新前已经添加但尚未保存的空 key 草稿，由系统在保存前自动补齐标识。
  guestFieldDrafts.value.forEach((field) => {
    if (!field.key.trim()) {
      field.key = createGuestFieldKey()
    }
  })
  const normalizedFields = guestFieldDrafts.value.map(({ label, key, type, required, visibleToGuest, isEnabled }) => ({
    label: label.trim(),
    key: key.trim(),
    type,
    required,
    visibleToGuest,
    isEnabled,
  }))
  if (normalizedFields.some((field) => !field.label)) {
    guestFieldMessageType.value = 'error'
    guestFieldMessage.value = '请填写每个新增字段的名称。'
    return
  }
  if (normalizedFields.some((field) => !/^[a-z][a-z0-9_]*$/.test(field.key))) {
    guestFieldMessageType.value = 'error'
    guestFieldMessage.value = '字段标识必须以小写字母开头，并且只能包含小写字母、数字和下划线。'
    return
  }
  const fieldKeys = normalizedFields.map((field) => field.key)
  if (new Set(fieldKeys).size !== fieldKeys.length) {
    guestFieldMessageType.value = 'error'
    guestFieldMessage.value = '字段标识不能重复。'
    return
  }

  savingGuestFields.value = true
  guestFieldMessage.value = ''
  try {
    let savedFields = fields.value
    // 只有字段定义发生变化时才同步动态字段，减少不必要的接口请求。
    if (guestFieldDefinitionsChanged.value) {
      savedFields = await replaceAdminGuestFields(meeting.value.id, normalizedFields)
    }
    const savedDisplayFields = await replaceAdminGuestDisplayFields(
      meeting.value.id,
      selectedGuestDisplayFieldKeys(),
    )
    const savedRegistrationSettings = await replaceAdminGuestRegistrationSettings(
      meeting.value.id,
      currentFixedGuestRegistrationSettings(),
    )
    fields.value = savedFields
    savedVisibleGuestFieldKeys.value = savedDisplayFields
    savedGuestRegistrationSettings.value = savedRegistrationSettings
    resetGuestFieldDrafts(savedFields, savedDisplayFields, savedRegistrationSettings)
    guestFieldMessageType.value = 'success'
    guestFieldMessage.value = '嘉宾字段及嘉宾端呈现设置已保存。'
  } catch (error) {
    guestFieldMessageType.value = 'error'
    guestFieldMessage.value = getApiErrorMessage(error, '嘉宾字段保存失败。')
  } finally {
    savingGuestFields.value = false
  }
}

/**
 * 打开单项会议助手配置编辑窗口。
 *
 * 入参：feature 为管理员选中的会议助手功能，必填。
 * 返回值：void：复制当前配置到表单并显示编辑弹窗。
 * 异常：当前函数不主动抛出异常。
 */
function openAssistantEditDialog(feature: MeetingAssistantFeature): void {
  selectedAssistantFeature.value = feature
  assistantMaterialCount.value = 0
  assistantEditForm.value = {
    content: feature.key === 'route' ? decodeMaterialRichContent(feature.content) : feature.content,
    unpublishedMessage: feature.unpublishedMessage,
    isPublished: feature.isPublished,
    accessLevel: feature.accessLevel,
    contactQrTitle: feature.contactQrTitle || '会务二维码',
    contacts: feature.contacts.length
      ? feature.contacts.map((item) => createContactRow(item))
      : [createContactRow()],
  }
  void refreshContactQrPreview(feature)
  assistantEditDialogVisible.value = true
}

/**
 * 在联系会务编辑表单中添加一个空联系人行。
 *
 * 入参：无。
 * 返回值：void：向 contacts 追加空白行。
 * 异常：当前函数不主动抛出异常。
 */
function addContactPerson(): void {
  assistantEditForm.value.contacts.push(createContactRow())
}

/**
 * 从联系会务编辑表单中删除指定联系人。
 *
 * 入参：index 为待删除联系人的索引，必填。
 * 返回值：void：更新 contacts 列表；至少保留一行。
 * 异常：当前函数不主动抛出异常。
 */
function removeContactPerson(index: number): void {
  if (assistantEditForm.value.contacts.length <= 1) {
    assistantEditForm.value.contacts = [createContactRow()]
    return
  }
  assistantEditForm.value.contacts.splice(index, 1)
}

/**
 * 释放联系会务二维码预览地址。
 *
 * 入参：无。
 * 返回值：void：存在本地预览地址时释放并清空。
 * 异常：当前函数不主动抛出异常。
 */
function revokeContactQrPreviewUrl(): void {
  if (contactQrPreviewUrl.value) {
    URL.revokeObjectURL(contactQrPreviewUrl.value)
    contactQrPreviewUrl.value = ''
  }
}

/**
 * 刷新联系会务二维码预览图。
 *
 * 入参：feature 为联系会务功能配置，必填。
 * 返回值：Promise<void>：有二维码时读取图片并生成本地预览地址，无二维码时清空预览。
 * 异常：图片读取失败时静默清空预览，避免影响联系人编辑。
 */
async function refreshContactQrPreview(feature: MeetingAssistantFeature): Promise<void> {
  revokeContactQrPreviewUrl()
  if (feature.key !== 'contact' || !feature.contactQrOriginalFilename || !meeting.value) {
    return
  }
  try {
    contactQrPreviewUrl.value = await fetchContactQrObjectUrl(meeting.value.id, 'admin')
  } catch {
    contactQrPreviewUrl.value = ''
  }
}

/**
 * 将联系会务最新配置同步到当前弹窗和配置列表。
 *
 * 入参：feature 为后端返回的联系会务功能配置，必填。
 * 返回值：void：更新当前选择和会议服务列表中的同项数据。
 * 异常：当前函数不主动抛出异常。
 */
function syncSelectedAssistantFeature(feature: MeetingAssistantFeature): void {
  selectedAssistantFeature.value = feature
  assistantFeatures.value = assistantFeatures.value.map((item) => item.key === feature.key ? feature : item)
}

/**
 * 打开联系会务二维码文件选择框。
 *
 * 入参：无。
 * 返回值：void：触发隐藏文件输入控件。
 * 异常：输入控件未挂载时不执行。
 */
function selectContactQrFile(): void {
  contactQrInput.value?.click()
}

/**
 * 响应管理员选择联系会务二维码图片。
 *
 * 入参：event 为文件输入变更事件，必填。
 * 返回值：Promise<void>：上传成功后刷新配置和预览。
 * 异常：会议未加载、格式不符或网络异常时展示错误提示。
 */
async function handleContactQrFileChange(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || !meeting.value) {
    return
  }
  uploadingContactQr.value = true
  try {
    const feature = await uploadAdminContactQr(meeting.value.id, file)
    syncSelectedAssistantFeature(feature)
    await refreshContactQrPreview(feature)
    ElMessage.success('会务二维码已上传。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '会务二维码上传失败。'))
  } finally {
    uploadingContactQr.value = false
  }
}

/**
 * 删除当前联系会务二维码图片。
 *
 * 入参：无。
 * 返回值：Promise<void>：删除成功后刷新配置并清空预览。
 * 异常：会议未加载、权限或网络异常时展示错误提示。
 */
async function removeContactQrImage(): Promise<void> {
  if (!meeting.value) {
    return
  }
  deletingContactQr.value = true
  try {
    const feature = await deleteAdminContactQr(meeting.value.id)
    syncSelectedAssistantFeature(feature)
    revokeContactQrPreviewUrl()
    ElMessage.success('会务二维码已删除。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '会务二维码删除失败。'))
  } finally {
    deletingContactQr.value = false
  }
}

/**
 * 保存会议助手正文、未发布提醒和发布状态。
 *
 * 入参：无；函数读取当前会议、选中功能和编辑表单。
 * 返回值：Promise<void>：保存成功后刷新配置列表并关闭弹窗。
 * 异常：提醒为空、已发布内容为空、登录过期、权限或网络异常时展示错误提示。
 */
async function saveAssistantFeature(): Promise<void> {
  if (!meeting.value || !selectedAssistantFeature.value) {
    return
  }
  const content = selectedAssistantFeature.value.key === 'route'
    ? encodeMaterialRichContent(assistantEditForm.value.content)
    : assistantEditForm.value.content.trim()
  const unpublishedMessage = assistantEditForm.value.unpublishedMessage.trim()
  const contacts = assistantEditForm.value.contacts
    .map((item) => ({
      name: item.name.trim(),
      role: item.role.trim(),
      phone: item.phone.trim(),
    }))
    .filter((item) => item.name)
  if (!unpublishedMessage) {
    ElMessage.warning('请填写未发布时向嘉宾展示的提醒。')
    return
  }
  if (selectedAssistantFeature.value.key === 'contact') {
    if (
      assistantEditForm.value.isPublished
      && contacts.length === 0
      && !selectedAssistantFeature.value.contactQrOriginalFilename
    ) {
      ElMessage.warning('发布前请至少添加一位联系人或上传会务二维码。')
      return
    }
  } else if (selectedAssistantFeature.value.key === 'manual') {
    if (assistantEditForm.value.isPublished && assistantMaterialCount.value === 0) {
      ElMessage.warning('发布前请至少添加一份会议资料。')
      return
    }
  } else if (assistantEditForm.value.isPublished && !content) {
    ElMessage.warning('发布前请填写功能内容。')
    return
  }
  savingAssistantFeature.value = true
  assistantError.value = ''
  try {
    const savedFeature = await updateAdminMeetingAssistantFeature(
      meeting.value.id,
      selectedAssistantFeature.value.key,
      {
        content: selectedAssistantFeature.value.key === 'contact'
          ? ''
          : selectedAssistantFeature.value.key === 'manual'
            ? selectedAssistantFeature.value.content
            : content,
        unpublishedMessage,
        isPublished: assistantEditForm.value.isPublished,
        accessLevel: assistantEditForm.value.accessLevel,
        contacts: selectedAssistantFeature.value.key === 'contact' ? contacts : [],
        contactQrTitle: assistantEditForm.value.contactQrTitle.trim() || '会务二维码',
      },
    )
    assistantFeatures.value = await listAdminMeetingAssistantFeatures(meeting.value.id)
    assistantEditDialogVisible.value = false
    ElMessage.success(savedFeature.isPublished ? '会议助手内容已保存并发布。' : '会议助手草稿和提醒已保存。')
  } catch (error) {
    assistantError.value = getApiErrorMessage(error, '会议助手配置保存失败。')
    ElMessage.error(assistantError.value)
  } finally {
    savingAssistantFeature.value = false
  }
}

/**
 * 在草稿与已发布状态之间切换会议编辑表单。
 *
 * 入参：无；函数读取当前表单中的会议状态。
 * 返回值：void：草稿切换为已发布，已发布切换为草稿；已结束会议保持不变。
 * 异常：当前函数不主动抛出异常；最终状态仍需点击保存并由后端校验。
 */
async function toggleMeetingPublishStatus(): Promise<void> {
  // 已结束会议不允许通过发布按钮重新进入草稿或发布状态。
  if (editForm.value.status === 'ended') {
    return
  }
  const willPublish = editForm.value.status !== 'published'
  const title = willPublish ? '发布会议' : '撤回为草稿'
  const message = willPublish
    ? '发布会场后，嘉宾和工作人员即可通过二维码或链接进入，是否继续？'
    : '撤回为草稿后，访问入口将立即失效，嘉宾无法继续扫码或打开链接，是否继续？'
  const confirmText = willPublish ? '发布' : '撤回为草稿'
  const cancelText = '取消'
  try {
    await ElMessageBox.confirm(message, title, {
      type: 'warning',
      confirmButtonText: confirmText,
      cancelButtonText: cancelText,
      customClass: 'meeting-edit-publish-confirm',
    })
  } catch {
    // 用户取消时不做任何调整
    return
  }
  // 先在表单中切换状态，再立刻保存到后端
  editForm.value.status = willPublish ? 'published' : 'draft'
  await saveMeeting({ silent: true })
}

/**
 * 使用当前会议数据重置编辑表单。
 *
 * 入参：
 *   无；函数读取当前页面的会议详情。
 *
 * 返回值：
 *   void：只更新页面编辑表单。
 *
 * 异常：
 *   当前函数不主动抛出异常；会议未加载时直接返回。
 */
function resetEditForm(): void {
  if (!meeting.value) {
    return
  }

  editForm.value = {
    title: meeting.value.title,
    description: meeting.value.description,
    location: meeting.value.location,
    navigationName: meeting.value.navigationName,
    navigationAddress: meeting.value.navigationAddress,
    navigationLongitude: meeting.value.navigationLongitude,
    navigationLatitude: meeting.value.navigationLatitude,
    startTime: toDateTimeLocalValue(meeting.value.startTime),
    endTime: toDateTimeLocalValue(meeting.value.endTime),
    timeDisplayMode: meeting.value.timeDisplayMode,
    status: meeting.value.status,
    registrationEnabled: Boolean(meeting.value.registrationEnabled),
    publicUrl: meeting.value.publicUrl || '',
  }
  // 编辑框默认显示当前浏览器地址（部署到服务器后即为本机 IP）；已保存的自定义地址优先
  publicUrlEdit.value = meeting.value.publicUrl || getDefaultPublicBaseUrl()
  saveMessage.value = ''
}

/**
 * 保存会议基础信息编辑结果。
 *
 * 入参：
 *   options.silent - 静默保存：用于发布/撤回场景，不展示顶部提示文案，避免与确认弹窗叠加。
 *
 * 返回值：
 *   Promise<void>：保存成功后刷新页面会议详情并展示结果提示；silent 为真时不展示顶部提示。
 *
 * 异常：
 *   字段、时间、权限、登录或网络无效时展示后端错误提示。
 */
async function saveMeeting(options: { silent?: boolean } = {}): Promise<void> {
  if (!editForm.value.title.trim() || !editForm.value.location.trim()) {
    saveMessageType.value = 'error'
    saveMessage.value = '会议名称和地点不能为空。'
    return
  }

  saving.value = true
  saveMessage.value = ''
  try {
    const savedMeeting = await updateAdminMeeting(String(route.params.id), {
      title: editForm.value.title.trim(),
      description: editForm.value.description.trim(),
      location: editForm.value.location.trim(),
      navigationName: editForm.value.navigationName,
      navigationAddress: editForm.value.navigationAddress,
      navigationLongitude: editForm.value.navigationLongitude,
      navigationLatitude: editForm.value.navigationLatitude,
      startTime: toIsoWithChinaTimezone(editForm.value.startTime),
      endTime: toIsoWithChinaTimezone(editForm.value.endTime),
      timeDisplayMode: editForm.value.timeDisplayMode,
      status: editForm.value.status,
      registrationEnabled: editForm.value.registrationEnabled,
      publicUrl: publicUrlEdit.value.trim() || undefined,
    })
    meeting.value = savedMeeting
    resetEditForm()
    if (!options.silent) {
      saveMessageType.value = 'success'
      saveMessage.value = '会议信息已保存。'
    }
  } catch (error) {
    saveMessageType.value = 'error'
    saveMessage.value = getApiErrorMessage(error, '会议信息保存失败。')
    ElMessage.error(saveMessage.value)
  } finally {
    saving.value = false
  }
}

/**
 * 打开导航地点搜索窗口，并使用当前会议地点作为默认关键词。
 *
 * 入参：无。
 * 返回值：void：初始化搜索状态并显示地点选择窗口。
 * 异常：当前函数不主动抛出异常。
 */
function openLocationDialog(): void {
  locationSearchQuery.value = editForm.value.navigationName || editForm.value.location
  locationOptions.value = []
  locationSearchError.value = ''
  locationDialogVisible.value = true
}

/**
 * 调用后端高德代理搜索导航地点候选项。
 *
 * 入参：无；函数读取地点搜索关键词。
 * 返回值：Promise<void>：成功后更新最多十条候选地点。
 * 异常：关键词过短、高德未配置、权限或网络异常时展示中文错误。
 */
async function searchLocationOptions(): Promise<void> {
  const query = locationSearchQuery.value.trim()
  if (query.length < 2) {
    locationSearchError.value = '请输入至少两个字符的地点关键词。'
    return
  }
  locationSearching.value = true
  locationSearchError.value = ''
  try {
    locationOptions.value = await searchMeetingLocationOptions(String(route.params.id), query)
    if (!locationOptions.value.length) {
      locationSearchError.value = '没有找到匹配地点，请补充城市或详细地址后重试。'
    }
  } catch (error) {
    locationOptions.value = []
    locationSearchError.value = getApiErrorMessage(error, '地点搜索失败，请稍后重试。')
  } finally {
    locationSearching.value = false
  }
}

/**
 * 将管理员确认的高德地点写入会议编辑表单。
 *
 * 入参：option 为选中的高德地点候选项，必填。
 * 返回值：void：保存名称、地址和坐标并关闭选择窗口。
 * 异常：当前函数不主动抛出异常。
 */
function selectLocationOption(option: MeetingLocationOption): void {
  editForm.value.navigationName = option.name
  editForm.value.navigationAddress = `${option.district}${option.address}`
  editForm.value.navigationLongitude = option.longitude
  editForm.value.navigationLatitude = option.latitude
  locationDialogVisible.value = false
  saveMessage.value = '导航位置已选择，请点击“保存”写入会议。'
  saveMessageType.value = 'info'
}

/**
 * 清除当前编辑表单中的导航点位。
 *
 * 入参：无。
 * 返回值：void：清空导航名称、地址和坐标，保存会议后生效。
 * 异常：当前函数不主动抛出异常。
 */
function clearNavigationLocation(): void {
  editForm.value.navigationName = ''
  editForm.value.navigationAddress = ''
  editForm.value.navigationLongitude = undefined
  editForm.value.navigationLatitude = undefined
  saveMessage.value = '导航位置已清除，请点击“保存”确认。'
  saveMessageType.value = 'info'
}

/**
 * 创建包含当前启用动态字段的嘉宾表单初始值。
 *
 * 入参：sourceValues 为已有动态字段值，可为空；缺少的当前启用字段初始化为空字符串。
 * 返回值：GuestFormState：固定字段为空且动态字段结构完整的表单对象。
 * 异常：当前函数不主动抛出异常；未知历史字段不会进入当前编辑表单。
 */
function createGuestFormState(sourceValues: Record<string, string | null> = {}): GuestFormState {
  return {
    name: '',
    phone: '',
    organization: '',
    title: '',
    tag: '',
    seat: '',
    values: Object.fromEntries(
      fields.value
        .filter((field) => field.isEnabled)
        .map((field) => [field.key, sourceValues[field.key] ?? '']),
    ),
  }
}

/**
 * 校验嘉宾表单中的当前启用动态必填字段。
 *
 * 入参：form 为新增或编辑嘉宾表单，必填。
 * 返回值：string：全部填写时返回空字符串，否则返回第一个缺失字段名称。
 * 异常：当前函数不主动抛出异常；空值和纯空白文本均视为未填写。
 */
function findMissingRequiredDynamicField(form: GuestFormState): string {
  return enabledDynamicGuestFields.value.find(
    (field) => field.required && !String(form.values[field.key] ?? '').trim(),
  )?.label ?? ''
}

/**
 * 打开新增嘉宾弹窗并按当前字段配置重建空白表单。
 *
 * 入参：无。
 * 返回值：void：显示弹窗并确保新增字段无需刷新页面即可填写。
 * 异常：当前函数不主动抛出异常。
 */
function openGuestCreateDialog(): void {
  guestForm.value = createGuestFormState()
  guestCreateDialogVisible.value = true
}

/**
 * 打开嘉宾详情窗口并生成该嘉宾的个人签到二维码。
 *
 * 入参：guest 为当前列表选中的嘉宾，必填；函数使用其 ID 查询完整资料。
 * 返回值：Promise<void>：详情读取完成后更新嘉宾信息和二维码图片。
 * 异常：权限、网络或二维码生成失败时关闭加载状态并展示错误提示。
 */
async function showGuestDetail(guest: Guest): Promise<void> {
  selectedGuest.value = undefined
  guestQrCode.value = ''
  guestDetailDialogVisible.value = true
  guestDetailLoading.value = true
  try {
    const guestDetail = await getAdminGuest(guest.meetingId, guest.id)
    selectedGuest.value = guestDetail
    guestQrCode.value = await QRCode.toDataURL(guestDetail.qrToken, { width: 220, margin: 1 })
  } catch (error) {
    guestQrCode.value = ''
    guestDetailDialogVisible.value = false
    ElMessage.error(getApiErrorMessage(error, '嘉宾详情或二维码加载失败。'))
  } finally {
    guestDetailLoading.value = false
  }
}

/**
 * 打开嘉宾编辑弹窗并读取完整固定资料与动态字段值。
 *
 * 入参：guest 为列表中选中的正式嘉宾，必填。
 * 返回值：Promise<void>：读取完成后填充表单并保持弹窗可编辑。
 * 异常：权限、网络或嘉宾不存在时关闭弹窗并展示中文错误。
 */
async function openGuestEditDialog(guest: Guest): Promise<void> {
  editingGuest.value = guest
  guestEditDialogVisible.value = true
  guestEditLoading.value = true
  try {
    const detail = await getAdminGuest(guest.meetingId, guest.id)
    guestEditForm.value = {
      ...createGuestFormState(detail.values),
      name: detail.name,
      phone: detail.phone,
      organization: detail.organization,
      title: detail.title,
      tag: detail.tag,
      seat: detail.seat,
    }
  } catch (error) {
    guestEditDialogVisible.value = false
    editingGuest.value = undefined
    ElMessage.error(getApiErrorMessage(error, '嘉宾完整信息加载失败。'))
  } finally {
    guestEditLoading.value = false
  }
}

/**
 * 保存嘉宾编辑弹窗中的固定资料并刷新列表。
 *
 * 入参：无；函数读取当前会议、编辑目标和编辑表单。
 * 返回值：Promise<void>：保存成功后关闭弹窗并刷新嘉宾与签到状态。
 * 异常：姓名或手机号为空时提示补充；权限、字段或网络异常时展示错误提示。
 */
async function handleUpdateGuest(): Promise<void> {
  if (!meeting.value || !editingGuest.value) {
    return
  }
  if (!guestEditForm.value.name.trim() || !guestEditForm.value.phone.trim()) {
    ElMessage.warning('请填写嘉宾姓名和手机号。')
    return
  }
  const missingDynamicField = findMissingRequiredDynamicField(guestEditForm.value)
  if (missingDynamicField) {
    ElMessage.warning(`请填写${missingDynamicField}。`)
    return
  }
  updatingGuest.value = true
  try {
    await updateAdminGuest(meeting.value.id, editingGuest.value.id, guestEditForm.value)
    await refreshGuestAndCheckInState(meeting.value.id)
    guestEditDialogVisible.value = false
    editingGuest.value = undefined
    ElMessage.success('嘉宾信息已保存。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '嘉宾信息保存失败。'))
  } finally {
    updatingGuest.value = false
  }
}

/**
 * 经管理员确认后软删除嘉宾并刷新当前名单。
 *
 * 入参：guest 为待删除的正式嘉宾，必填。
 * 返回值：Promise<void>：确认并删除成功后刷新嘉宾与签到状态。
 * 异常：管理员取消时静默结束；权限、资源或网络异常时展示错误提示。
 */
async function handleDeleteGuest(guest: Guest): Promise<void> {
  if (!meeting.value) {
    return
  }
  try {
    await ElMessageBox.confirm(
      `删除“${guest.name}”后，该嘉宾将无法登录或签到，历史签到记录仍会保留。是否继续？`,
      '删除嘉宾',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    await deleteAdminGuest(meeting.value.id, guest.id)
    await refreshGuestAndCheckInState(meeting.value.id)
    if (selectedGuest.value?.id === guest.id) {
      guestDetailDialogVisible.value = false
      selectedGuest.value = undefined
    }
    if (editingGuest.value?.id === guest.id) {
      guestEditDialogVisible.value = false
      editingGuest.value = undefined
    }
    ElMessage.success('嘉宾已删除。')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(getApiErrorMessage(error, '嘉宾删除失败。'))
    }
  }
}

/**
 * 创建嘉宾并刷新当前会议嘉宾列表。
 *
 * 入参：无；读取当前会议和新增嘉宾表单。
 * 返回值：Promise<void>：创建完成后关闭弹窗并更新列表。
 * 异常：姓名或手机号缺失、权限、登录或网络异常时显示错误提示。
 */
async function handleCreateGuest(): Promise<void> {
  if (!meeting.value || !guestForm.value.name.trim() || !guestForm.value.phone.trim()) {
    ElMessage.warning('请填写嘉宾姓名和手机号。')
    return
  }
  const missingDynamicField = findMissingRequiredDynamicField(guestForm.value)
  if (missingDynamicField) {
    ElMessage.warning(`请填写${missingDynamicField}。`)
    return
  }
  creatingGuest.value = true
  try {
    await createAdminGuest(meeting.value.id, guestForm.value)
    await refreshGuestAndCheckInState(meeting.value.id)
    guestForm.value = createGuestFormState()
    guestCreateDialogVisible.value = false
    ElMessage.success('嘉宾已新增，并已生成个人二维码。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '嘉宾新增失败。'))
  } finally {
    creatingGuest.value = false
  }
}

/**
 * 创建工作人员账号并授权其负责当前会议。
 *
 * 入参：无；读取当前会议与工作人员表单。
 * 返回值：Promise<void>：创建后刷新工作人员列表并展示结果。
 * 异常：必填字段缺失、会议不存在或账号重复时展示错误提示。
 */
async function handleCreateStaff(): Promise<void> {
  if (!meeting.value || !staffForm.value.account.trim() || staffForm.value.initialPassword.length < 8) {
    staffMessageType.value = 'error'
    staffMessage.value = '请填写登录账号和至少 8 位初始密码。'
    return
  }
  creatingStaff.value = true
  staffMessage.value = ''
  try {
    await createAdminStaff(meeting.value.id, {
      username: staffForm.value.account.trim(),
      initialPassword: staffForm.value.initialPassword,
      displayName: staffForm.value.displayName,
    })
    staff.value = await listAdminStaff(meeting.value.id)
    staffForm.value = { account: '', initialPassword: '', displayName: '' }
    staffMessageType.value = 'success'
    staffMessage.value = '工作人员已创建或复用，并授权当前会议。'
  } catch (error) {
    staffMessageType.value = 'error'
    staffMessage.value = getApiErrorMessage(error, '工作人员创建或授权失败。')
  } finally {
    creatingStaff.value = false
  }
}

/**
 * 打开工作人员编辑窗口并填充当前资料。
 *
 * 入参：currentStaff 为当前选中的工作人员，必填。
 * 返回值：void：更新编辑表单并显示弹窗。
 * 异常：当前函数不主动抛出异常。
 */
function openStaffEditDialog(currentStaff: StaffUser): void {
  selectedStaff.value = currentStaff
  staffEditForm.value = {
    isActive: currentStaff.isActive !== false,
    newPassword: '',
    displayName: currentStaff.displayName,
  }
  staffEditDialogVisible.value = true
}

/**
 * 保存工作人员资料、状态和可选的新密码。
 *
 * 入参：无；函数读取当前会议、选中工作人员和编辑表单。
 * 返回值：Promise<void>：保存成功后刷新列表并关闭弹窗。
 * 异常：姓名为空、新密码不足 8 位、权限或网络异常时展示页面提示。
 */
async function handleUpdateStaff(): Promise<void> {
  if (!meeting.value || !selectedStaff.value) {
    return
  }
  if (staffEditForm.value.newPassword && staffEditForm.value.newPassword.length < 8) {
    ElMessage.warning('新密码至少需要 8 位。')
    return
  }
  savingStaff.value = true
  try {
    await updateAdminStaff(meeting.value.id, selectedStaff.value.id, {
      isActive: staffEditForm.value.isActive,
      newPassword: staffEditForm.value.newPassword || undefined,
      displayName: staffEditForm.value.displayName,
    })
    staff.value = await listAdminStaff(meeting.value.id)
    staffEditDialogVisible.value = false
    ElMessage.success('工作人员资料已保存。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '工作人员资料保存失败。'))
  } finally {
    savingStaff.value = false
  }
}

/**
 * 经管理员确认后解除工作人员对当前会议的授权。
 *
 * 入参：currentStaff 为待解除授权的工作人员，必填。
 * 返回值：Promise<void>：确认并解除成功后刷新工作人员列表。
 * 异常：管理员取消时静默结束；权限、资源或网络异常时展示错误提示。
 */
async function handleRemoveStaff(currentStaff: StaffUser): Promise<void> {
  if (!meeting.value) {
    return
  }
  try {
    await ElMessageBox.confirm(`确认解除“${currentStaff.name}”对当前会议的授权吗？`, '解除工作人员授权', {
      confirmButtonText: '确认解除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await removeAdminStaffAssignment(meeting.value.id, currentStaff.id)
    staff.value = await listAdminStaff(meeting.value.id)
    ElMessage.success('工作人员会议授权已解除。')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(getApiErrorMessage(error, '工作人员授权解除失败。'))
    }
  }
}

/**
 * 下载包含标准列名的嘉宾 Excel 导入模板。
 *
 * 入参：无。
 *
 * 返回值：void：浏览器开始下载 xlsx 模板文件。
 *
 * 异常：当前函数不主动抛出异常；浏览器禁止下载时由浏览器提示。
 */
async function downloadGuestImportTemplate(): Promise<void> {
  if (!meeting.value) {
    return
  }
  try {
    await downloadAdminGuestImportTemplate(meeting.value.id, meeting.value.title)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '嘉宾导入模板下载失败。'))
  }
}

/**
 * 打开嘉宾 Excel 导入弹窗并清理上一次导入结果。
 *
 * 入参：无。
 * 返回值：void：保持当前嘉宾管理区块不变并显示导入弹窗。
 * 异常：当前函数不主动抛出异常。
 */
function openGuestImportDialog(): void {
  importMessage.value = ''
  guestImportDialogVisible.value = true
}

/**
 * 打开系统文件选择器，以便管理员选择待导入的 Excel 文件。
 *
 * 入参：无。
 *
 * 返回值：void：触发隐藏文件输入框的点击事件。
 *
 * 异常：当前函数不主动抛出异常；输入框未挂载时直接返回。
 */
function openGuestImportFilePicker(): void {
  guestImportInput.value?.click()
}

/**
 * 将管理员选择的 Excel 文件上传后端并展示逐行导入结果。
 *
 * 入参：
 *   event：文件输入框变化事件，必填。
 *
 * 返回值：Promise<void>：导入结束后刷新嘉宾列表并显示结果摘要。
 *
 * 异常：
 *   文件格式、大小、表头、字段值、权限或网络异常时显示后端错误提示。
 */
async function handleGuestImportFileChange(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file || !meeting.value) {
    return
  }

  importing.value = true
  importMessage.value = ''

  try {
    const result = await importAdminGuests(meeting.value.id, file)
    await refreshGuestAndCheckInState(meeting.value.id)
    importMessageType.value = result.errors.length ? 'warning' : 'success'
    importMessage.value = result.errors.length
      ? `成功导入 ${result.importedCount} 名嘉宾；${result.errors.map((item) => `第 ${item.rowNumber} 行：${item.message}`).join('；')}`
      : `成功导入 ${result.importedCount} 名嘉宾。`
  } catch (error) {
    importMessageType.value = 'error'
    importMessage.value = getApiErrorMessage(error, '导入失败，请检查 Excel 文件后重试。')
  } finally {
    importing.value = false
    input.value = ''
  }
}

/**
 * 将当前会议的全量嘉宾签到表导出为 xlsx 文件。
 *
 * 入参：
 *   无；函数读取已加载的会议、嘉宾和签到记录。
 *
 * 返回值：
 *   Promise<void>：后端生成并下载 Excel 文件后结束。
 *
 * 异常：
 *   会议未加载、权限或网络失败时展示页面提示，不向页面外抛出异常。
 *
 * 示例：
 *   await handleExportCheckInSheet()
 */
async function handleExportCheckInSheet(): Promise<void> {
  if (!meeting.value) {
    ElMessage.warning('未找到会议，无法导出签到表。')
    return
  }

  exporting.value = true

  try {
    await downloadAdminCheckInExport(meeting.value.id, meeting.value.title)
    ElMessage.success('嘉宾签到表已开始下载。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '签到表导出失败，请稍后重试。'))
  } finally {
    exporting.value = false
  }
}

/**
 * 将当前会议的嘉宾信息与管理状态导出为 xlsx 文件。
 *
 * 入参：
 *   无；函数读取当前已加载会议。
 *
 * 返回值：
 *   Promise<void>：后端生成并下载嘉宾状态表后结束。
 *
 * 异常：
 *   会议未加载、权限或网络失败时展示页面提示，不向页面外抛出异常。
 *
 * 示例：
 *   await handleExportGuestStatusSheet()
 */
async function handleExportGuestStatusSheet(): Promise<void> {
  if (!meeting.value) {
    ElMessage.warning('未找到会议，无法导出嘉宾状态表。')
    return
  }

  exporting.value = true

  try {
    await downloadAdminGuestStatusExport(meeting.value.id, meeting.value.title)
    ElMessage.success('嘉宾状态表已开始下载。')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '嘉宾状态表导出失败，请稍后重试。'))
  } finally {
    exporting.value = false
  }
}

/**
 * 跳转到管理员登录页。
 *
 * 入参：
 *   无。
 *
 * 返回值：
 *   void：只触发前端路由跳转。
 *
 * 异常：
 *   当前函数不主动抛出异常。
 */
function goLogin(): void {
  router.push('/login')
}

/**
 * 返回管理员会议管理列表。
 *
 * 入参：无。
 * 返回值：void：触发前端路由跳转。
 * 异常：当前函数不主动抛出异常。
 */
function goMeetings(): void {
  router.push('/admin/meetings')
}

/**
 * 复制当前已发布会议的公开入口链接。
 *
 * 入参：无；函数读取当前会议入口链接。
 * 返回值：Promise<void>：复制完成后展示操作结果。
 * 异常：浏览器不允许访问剪贴板时展示错误提示。
 */
async function copyMeetingEntryUrl(): Promise<void> {
  try {
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(meetingEntryUrl.value)
      } catch {
        copyMeetingEntryUrlBySelection()
      }
    } else {
      copyMeetingEntryUrlBySelection()
    }
    ElMessage.success('会议入口链接已复制。')
  } catch {
    ElMessage.error('复制失败，请手动复制链接。')
  }
}

/**
 * 使用文本选择方式复制会议入口链接，兼容不允许异步剪贴板访问的浏览器。
 *
 * 入参：无；函数读取当前会议入口链接。
 * 返回值：void：执行浏览器复制命令。
 * 异常：浏览器拒绝复制命令时抛出异常，由调用方展示错误提示。
 */
function copyMeetingEntryUrlBySelection(): void {
  const textArea = document.createElement('textarea')
  textArea.value = meetingEntryUrl.value
  document.body.appendChild(textArea)
  textArea.select()
  const copied = document.execCommand('copy')
  textArea.remove()
  if (!copied) {
    throw new Error('浏览器拒绝复制命令。')
  }
}

/**
 * 打开会议二维码查看与下载窗口。
 *
 * 入参：无。
 * 返回值：void：显示会议二维码弹窗。
 * 异常：当前函数不主动抛出异常。
 */
function openMeetingQrDialog(): void {
  // 历史兼容保留，不再被调用
}

/**
 * 下载当前会议入口二维码图片。
 *
 * 入参：无；函数读取已生成的二维码数据地址和会议 ID。
 * 返回值：Promise<void>：生成包含会议标题、二维码和时间的 PNG 后触发下载。
 * 异常：二维码尚未生成、图片加载或画布创建失败时展示提示。
 */
async function downloadMeetingQrCode(): Promise<void> {
  if (!meetingQrCode.value || !meeting.value) {
    ElMessage.warning('二维码尚未生成。')
    return
  }
  const currentMeeting = meeting.value
  const canvas = document.createElement('canvas')
  const width = 600
  const height = 780
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext('2d')
  if (!context) {
    ElMessage.error('二维码下载失败，请稍后重试。')
    return
  }
  context.fillStyle = '#ffffff'
  context.fillRect(0, 0, width, height)
  context.fillStyle = '#111827'
  context.textAlign = 'center'
  context.font = '600 30px "Microsoft YaHei"'
  context.fillText(currentMeeting.title, width / 2, 64)
  let image: HTMLImageElement
  try {
    image = await loadQrImage(meetingQrCode.value)
  } catch {
    ElMessage.error('二维码下载失败，请稍后重试。')
    return
  }
  context.drawImage(image, 110, 110, 380, 380)
  context.fillStyle = '#4b5563'
  context.font = '24px "Microsoft YaHei"'
  context.fillText(`${formatDate(currentMeeting.startTime)} - ${formatDate(currentMeeting.endTime)}`, width / 2, 560)
  const link = document.createElement('a')
  link.href = canvas.toDataURL('image/png')
  link.download = `${currentMeeting.title.replace(/[\\/:*?"<>|]/g, '_')}-会议入口二维码.png`
  link.click()
}

/**
 * 加载二维码数据地址对应的图片，供下载排版画布绘制。
 *
 * 入参：source 为二维码图片数据地址，必填。
 * 返回值：Promise<HTMLImageElement>：成功加载的图片对象。
 * 异常：图片加载失败时拒绝 Promise。
 */
function loadQrImage(source: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('二维码图片加载失败。'))
    image.src = source
  })
}

/**
 * 根据已发布会议入口链接生成可扫码的二维码图片。
 *
 * 入参：entryUrl 为会议入口 URL，必填；为空或会议未发布时清空二维码。
 * 返回值：Promise<void>：完成后更新页面二维码数据地址。
 * 异常：二维码生成失败时清空图片并提示管理员。
 */
async function generateMeetingEntryQrCode(entryUrl: string): Promise<void> {
  if (!meeting.value || meeting.value.status !== 'published' || !entryUrl) {
    meetingQrCode.value = ''
    return
  }
  try {
    meetingQrCode.value = await QRCode.toDataURL(entryUrl, { width: 220, margin: 1 })
  } catch {
    meetingQrCode.value = ''
    ElMessage.error('会议二维码生成失败，请稍后重试。')
  }
}

/**
 * 格式化日期时间展示。
 *
 * 入参：value：ISO 日期字符串，必填。
 *
 * 返回值：string：中文本地化日期时间。
 *
 * 异常：当前函数不主动抛出异常。
 */
function formatDate(value: string): string {
  return new Date(value).toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}

/**
 * 将会议状态转换为当前会议卡片使用的中文说明。
 *
 * 入参：status 为会议状态，必填。
 * 返回值：string：草稿、已发布或已结束对应的中文状态文本。
 * 异常：当前函数不主动抛出异常。
 */
function statusText(status: MeetingStatus): string {
  const statusMap: Record<MeetingStatus, string> = {
    draft: '筹备中',
    published: '进行中',
    ended: '已结束',
  }
  return statusMap[status]
}

/**
 * 将 ISO 日期字符串转换为 datetime-local 控件可识别的值。
 *
 * 入参：
 *   value：ISO 日期字符串，必填。
 *
 * 返回值：
 *   string：形如 yyyy-MM-ddTHH:mm 的本地表单值。
 *
 * 异常：
 *   当前函数不主动抛出异常；空值会返回空字符串。
 */
function toDateTimeLocalValue(value: string): string {
  return value.slice(0, 16)
}

/**
 * 将 datetime-local 表单值转换为带中国时区偏移的 ISO 字符串。
 *
 * 入参：
 *   value：datetime-local 表单值，必填，格式通常为 yyyy-MM-ddTHH:mm。
 *
 * 返回值：
 *   string：形如 yyyy-MM-ddTHH:mm:00+08:00 的时间字符串。
 *
 * 异常：
 *   当前函数不主动抛出异常；空值会返回空字符串。
 */
function toIsoWithChinaTimezone(value: string): string {
  return value ? `${value}:00+08:00` : ''
}

onMounted(loadDetail)
onBeforeUnmount(revokeContactQrPreviewUrl)

/**
 * 主动触发会议入口二维码生成，调用方为边栏"生成二维码"按钮。
 */
async function regenerateMeetingEntryQrCode(): Promise<void> {
  if (!meeting.value || !meetingEntryUrl.value) {
    ElMessage.warning('请先填写公开访问链接。')
    return
  }
  regeneratingQr.value = true
  try {
    await generateMeetingEntryQrCode(meetingEntryUrl.value)
    ElMessage.success('二维码已生成。')
  } finally {
    regeneratingQr.value = false
  }
}
</script>
