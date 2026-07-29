<template>
  <section class="materials-editor">
    <header class="materials-editor__heading">
      <div>
        <h3>会议资料</h3>
        <p>每份资料可填写正文、上传附件，也可以同时提供两者。</p>
      </div>
      <el-button type="primary" plain :icon="Plus" @click="openCreateDialog">新增资料</el-button>
    </header>

    <el-alert v-if="errorMessage" type="error" :closable="false" :title="errorMessage" />
    <div v-loading="loading" class="materials-editor__list">
      <el-empty
        v-if="!loading && materials.length === 0"
        description="暂无会议资料，请点击“新增资料”"
        :image-size="72"
      />
      <article v-for="material in materials" :key="material.id" class="material-row">
        <div class="material-row__icon"><el-icon><Document /></el-icon></div>
        <div class="material-row__body">
          <strong>{{ material.title }}</strong>
          <p v-if="material.content">{{ meetingMaterialContentPreview(material.content) }}</p>
          <button
            v-if="material.originalFilename"
            type="button"
            class="material-row__attachment"
            :disabled="downloadingId === material.id"
            @click="downloadAttachment(material)"
          >
            <el-icon><Paperclip /></el-icon>
            <span>{{ material.originalFilename }}</span>
            <small>{{ formatFileSize(material.sizeBytes) }}</small>
          </button>
        </div>
        <div class="material-row__actions">
          <el-button link type="primary" @click="openEditDialog(material)">编辑</el-button>
          <el-button link type="danger" @click="removeMaterial(material)">删除</el-button>
        </div>
      </article>
    </div>

    <el-dialog
      v-model="formDialogVisible"
      append-to-body
      :title="editingMaterial ? '编辑资料' : '新增资料'"
      width="min(760px, calc(100% - 32px))"
      destroy-on-close
    >
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="资料标题" required>
          <el-input v-model="form.title" maxlength="200" show-word-limit placeholder="例如：参会须知" />
        </el-form-item>
        <el-form-item label="资料内容">
          <MeetingMaterialRichTextEditor
            v-model="form.content"
            label="资料内容"
          />
          <div class="el-form-item__help">
            支持段落、加粗、项目符号、编号、首行缩进 2 字符和整段缩进；不支持字体、颜色、图片和链接。
          </div>
        </el-form-item>
        <el-form-item label="可下载附件">
          <div class="material-upload">
            <input
              ref="fileInput"
              class="material-upload__input"
              type="file"
              :accept="attachmentAccept"
              @change="selectAttachment"
            />
            <el-button :icon="Upload" @click="fileInput?.click()">
              {{ form.attachment || form.existingFilename ? '更换附件' : '选择附件' }}
            </el-button>
            <span v-if="form.attachment" class="material-upload__filename">{{ form.attachment.name }}</span>
            <span v-else-if="form.existingFilename && !form.removeAttachment" class="material-upload__filename">
              {{ form.existingFilename }}
            </span>
            <el-button
              v-if="form.attachment || (form.existingFilename && !form.removeAttachment)"
              link
              type="danger"
              @click="clearAttachment"
            >
              移除
            </el-button>
          </div>
          <div class="el-form-item__help">支持 PDF、Office 文档、图片、文本和 ZIP，单个文件不超过 20MB。</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveMaterial">保存资料</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Document, Paperclip, Plus, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { getApiErrorMessage } from '../api/client'
import {
  createAdminMeetingMaterial,
  deleteAdminMeetingMaterial,
  downloadMeetingMaterialAttachment,
  listAdminMeetingMaterials,
  saveMeetingMaterialBlob,
  updateAdminMeetingMaterial,
} from '../api/meetingMaterials'
import type { MeetingMaterial } from '../types'
import MeetingMaterialRichTextEditor from './MeetingMaterialRichTextEditor.vue'
import {
  decodeMaterialRichContent,
  encodeMaterialRichContent,
  meetingMaterialContentPreview,
} from '../utils/materialRichText'

interface MaterialFormState {
  title: string
  content: string
  attachment?: File
  existingFilename: string
  removeAttachment: boolean
}

const props = defineProps<{ meetingId: string }>()
const emit = defineEmits<{ countChange: [count: number] }>()
const materials = ref<MeetingMaterial[]>([])
const loading = ref(false)
const saving = ref(false)
const downloadingId = ref('')
const errorMessage = ref('')
const formDialogVisible = ref(false)
const editingMaterial = ref<MeetingMaterial>()
const fileInput = ref<HTMLInputElement>()
const attachmentAccept = '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.png,.jpg,.jpeg'
const form = ref<MaterialFormState>(createEmptyForm())

/**
 * 创建新增资料使用的空白表单。
 *
 * 入参：无。
 * 返回值：MaterialFormState：标题、正文和附件均为空的初始表单。
 * 异常：当前函数不主动抛出异常。
 */
function createEmptyForm(): MaterialFormState {
  return {
    title: '',
    content: '',
    attachment: undefined,
    existingFilename: '',
    removeAttachment: false,
  }
}

/**
 * 从后端加载当前会议全部资料并同步资料数量。
 *
 * 入参：无；读取 props.meetingId。
 * 返回值：Promise<void>：成功后更新资料列表并向父组件发送数量。
 * 异常：权限、登录或网络异常时转换为组件内错误提示。
 */
async function loadMaterials(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    materials.value = await listAdminMeetingMaterials(props.meetingId)
    emit('countChange', materials.value.length)
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '会议资料加载失败。')
  } finally {
    loading.value = false
  }
}

/**
 * 打开新增资料编辑窗口。
 *
 * 入参：无。
 * 返回值：void：清空编辑对象和表单并显示窗口。
 * 异常：当前函数不主动抛出异常。
 */
function openCreateDialog(): void {
  editingMaterial.value = undefined
  form.value = createEmptyForm()
  formDialogVisible.value = true
}

/**
 * 打开指定资料的编辑窗口。
 *
 * 入参：material 为待编辑资料，必填。
 * 返回值：void：将历史或新版正文解码为安全文档 HTML，并复制附件名称后显示窗口。
 * 异常：当前函数不主动抛出异常。
 */
function openEditDialog(material: MeetingMaterial): void {
  editingMaterial.value = material
  form.value = {
    title: material.title,
    content: decodeMaterialRichContent(material.content),
    attachment: undefined,
    existingFilename: material.originalFilename,
    removeAttachment: false,
  }
  formDialogVisible.value = true
}

/**
 * 读取文件选择控件中的第一个附件。
 *
 * 入参：event 为原生文件输入 change 事件，必填。
 * 返回值：void：选择有效文件时写入表单；超过 20MB 时清空并提示。
 * 异常：当前函数不主动抛出异常。
 */
function selectAttachment(event: Event): void {
  const input = event.target as HTMLInputElement
  const selectedFile = input.files?.[0]
  if (!selectedFile) {
    return
  }
  if (selectedFile.size > 20 * 1024 * 1024) {
    input.value = ''
    ElMessage.warning('单个附件不能超过 20MB。')
    return
  }
  form.value.attachment = selectedFile
  form.value.removeAttachment = false
}

/**
 * 清除新选择的附件或标记删除已有附件。
 *
 * 入参：无。
 * 返回值：void：清空文件控件并更新删除附件标记。
 * 异常：当前函数不主动抛出异常。
 */
function clearAttachment(): void {
  form.value.attachment = undefined
  form.value.removeAttachment = Boolean(form.value.existingFilename)
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

/**
 * 校验表单并新增或更新会议资料。
 *
 * 入参：无；读取当前表单和编辑对象。
 * 返回值：Promise<void>：保存成功后关闭窗口并刷新资料列表。
 * 异常：字段、附件、权限或网络异常时展示中文提示。
 */
async function saveMaterial(): Promise<void> {
  const title = form.value.title.trim()
  const content = encodeMaterialRichContent(form.value.content)
  const keepsExistingAttachment = Boolean(form.value.existingFilename) && !form.value.removeAttachment
  if (!title) {
    ElMessage.warning('请填写资料标题。')
    return
  }
  if (!content && !form.value.attachment && !keepsExistingAttachment) {
    ElMessage.warning('资料内容和附件至少填写一项。')
    return
  }
  if (content.length > 20_000) {
    ElMessage.warning('排版后的资料内容过长，请精简后再保存。')
    return
  }
  saving.value = true
  try {
    const input = {
      title,
      content,
      attachment: form.value.attachment,
      removeAttachment: form.value.removeAttachment,
    }
    if (editingMaterial.value) {
      await updateAdminMeetingMaterial(props.meetingId, editingMaterial.value.id, input)
    } else {
      await createAdminMeetingMaterial(props.meetingId, input)
    }
    formDialogVisible.value = false
    ElMessage.success(editingMaterial.value ? '会议资料已更新。' : '会议资料已添加。')
    await loadMaterials()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '会议资料保存失败。'))
  } finally {
    saving.value = false
  }
}

/**
 * 二次确认后删除指定会议资料。
 *
 * 入参：material 为待删除资料，必填。
 * 返回值：Promise<void>：确认并删除成功后刷新列表；取消时直接结束。
 * 异常：权限或网络异常时展示中文提示。
 */
async function removeMaterial(material: MeetingMaterial): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `删除“${material.title}”后，正文和附件都将无法恢复。`,
      '删除会议资料',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    await deleteAdminMeetingMaterial(props.meetingId, material.id)
    ElMessage.success('会议资料已删除。')
    await loadMaterials()
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    ElMessage.error(getApiErrorMessage(error, '会议资料删除失败。'))
  }
}

/**
 * 下载管理员选择的会议资料附件。
 *
 * 入参：material 为包含附件的资料，必填。
 * 返回值：Promise<void>：获取附件后触发浏览器保存。
 * 异常：附件不存在、权限或网络异常时展示中文提示。
 */
async function downloadAttachment(material: MeetingMaterial): Promise<void> {
  if (!material.originalFilename) {
    return
  }
  downloadingId.value = material.id
  try {
    const blob = await downloadMeetingMaterialAttachment(props.meetingId, material.id, 'admin')
    saveMeetingMaterialBlob(blob, material.originalFilename)
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '附件下载失败。'))
  } finally {
    downloadingId.value = ''
  }
}

/**
 * 将附件字节数转换为易读的 KB 或 MB 文本。
 *
 * 入参：sizeBytes 为可空附件字节数。
 * 返回值：string：无大小时返回空字符串，否则返回保留一位小数的 KB 或 MB。
 * 异常：当前函数不主动抛出异常。
 */
function formatFileSize(sizeBytes?: number): string {
  if (!sizeBytes) {
    return ''
  }
  if (sizeBytes >= 1024 * 1024) {
    return `${(sizeBytes / 1024 / 1024).toFixed(1)} MB`
  }
  return `${Math.max(sizeBytes / 1024, 0.1).toFixed(1)} KB`
}

onMounted(loadMaterials)
</script>

<style scoped>
.materials-editor {
  display: grid;
  gap: 16px;
  margin-bottom: 20px;
}

.materials-editor__heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.materials-editor__heading h3 {
  margin: 0;
  color: #17211d;
  font-size: 16px;
}

.materials-editor__heading p {
  margin: 6px 0 0;
  color: #76807b;
  font-size: 13px;
}

.materials-editor__list {
  min-height: 100px;
}

.material-row {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: flex-start;
  padding: 16px;
  border: 1px solid #e6ebe8;
  border-radius: 10px;
  background: #fff;
}

.material-row + .material-row {
  margin-top: 10px;
}

.material-row__icon {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 9px;
  color: #07563f;
  background: #edf7f2;
  font-size: 20px;
}

.material-row__body {
  min-width: 0;
}

.material-row__body > strong {
  display: block;
  color: #17211d;
  font-size: 15px;
  line-height: 1.5;
}

.material-row__body > p {
  display: -webkit-box;
  overflow: hidden;
  margin: 6px 0 0;
  color: #68716d;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-line;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.material-row__attachment {
  display: inline-flex;
  max-width: 100%;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  padding: 0;
  border: 0;
  color: #07563f;
  background: transparent;
  cursor: pointer;
}

.material-row__attachment span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.material-row__attachment small {
  flex: none;
  color: #909995;
}

.material-row__actions {
  display: flex;
  flex: none;
}

.material-upload {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
}

.material-upload__input {
  display: none;
}

.material-upload__filename {
  min-width: 0;
  overflow: hidden;
  color: #52605a;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 640px) {
  .materials-editor__heading {
    align-items: stretch;
    flex-direction: column;
  }

  .material-row {
    grid-template-columns: 36px minmax(0, 1fr);
  }

  .material-row__icon {
    width: 36px;
    height: 36px;
  }

  .material-row__actions {
    grid-column: 2;
  }
}
</style>
