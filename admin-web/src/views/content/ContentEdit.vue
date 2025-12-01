<template>
  <div class="content-edit">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="page-title">编辑内容</span>
      </template>
    </el-page-header>

    <el-card class="edit-card" v-loading="loading">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        label-position="right"
      >
        <!-- 视频预览 -->
        <el-form-item label="视频">
          <div class="video-preview">
            <video v-if="form.video_url" :src="form.video_url" controls style="width: 100%; max-height: 300px" />
            <div class="video-info">
              <span>视频已上传，编辑时无法更换视频</span>
            </div>
          </div>
        </el-form-item>

        <!-- 封面图片 -->
        <el-form-item label="封面图片" prop="cover_url">
          <el-upload
            class="cover-uploader"
            :action="uploadAction"
            :headers="uploadHeaders"
            :on-success="handleCoverSuccess"
            :before-upload="beforeCoverUpload"
            :show-file-list="false"
            accept="image/jpeg,image/png"
          >
            <img v-if="form.cover_url" :src="form.cover_url" class="cover-image" />
            <div v-else class="cover-placeholder">
              <el-icon><Plus /></el-icon>
              <div class="cover-hint">上传封面</div>
            </div>
          </el-upload>
          <div class="form-hint">建议尺寸 16:9，支持 JPG、PNG 格式</div>
        </el-form-item>

        <!-- 标题 -->
        <el-form-item label="标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请输入内容标题"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <!-- 描述 -->
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            placeholder="请输入内容描述"
            :rows="4"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <!-- 内容类型 -->
        <el-form-item label="内容类型" prop="content_type">
          <el-select v-model="form.content_type" placeholder="请选择内容类型">
            <el-option label="工作知识" value="工作知识" />
            <el-option label="生活分享" value="生活分享" />
            <el-option label="企业文化" value="企业文化" />
          </el-select>
        </el-form-item>

        <!-- 标签 -->
        <el-form-item label="标签" prop="tags">
          <el-select
            v-model="form.tag_ids"
            multiple
            filterable
            placeholder="请选择标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in availableTags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>
          <div class="form-hint">可选择多个标签，帮助用户发现内容</div>
        </el-form-item>

        <!-- 状态 -->
        <el-form-item label="当前状态">
          <el-tag :type="getStatusType(form.status)">
            {{ getStatusText(form.status) }}
          </el-tag>
        </el-form-item>

        <!-- 精选内容 -->
        <el-form-item label="精选内容">
          <el-checkbox v-model="form.is_featured">
            标记为精选内容
          </el-checkbox>
          <div class="form-hint">精选内容将在首页推荐区域展示</div>
        </el-form-item>

        <!-- 显示优先级 -->
        <el-form-item label="显示优先级" v-if="form.is_featured">
          <el-input-number
            v-model="form.priority"
            :min="0"
            :max="100"
            placeholder="0-100"
          />
          <div class="form-hint">数值越大，显示优先级越高</div>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            保存
          </el-button>
          <el-button @click="goBack">取消</el-button>
          <el-button type="danger" @click="handleDelete" :loading="deleting">
            删除内容
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getContentDetail, updateContent, deleteContent } from '../../api/content'
import { getTagList } from '../../api/tag'

const router = useRouter()
const route = useRoute()

// 表单引用
const formRef = ref(null)

// 上传配置
const uploadAction = import.meta.env.VITE_API_BASE_URL + '/admin/contents/upload'
const uploadHeaders = computed(() => ({
  Authorization: 'Bearer ' + localStorage.getItem('admin_token')
}))

// 表单数据
const form = reactive({
  id: '',
  video_url: '',
  cover_url: '',
  title: '',
  description: '',
  content_type: '',
  tag_ids: [],
  status: '',
  is_featured: false,
  priority: 0
})

// 表单验证规则
const rules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' },
    { min: 1, max: 200, message: '标题长度在 1 到 200 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '描述不能超过 500 个字符', trigger: 'blur' }
  ],
  content_type: [
    { required: true, message: '请选择内容类型', trigger: 'change' }
  ]
}

// 状态
const loading = ref(false)
const submitting = ref(false)
const deleting = ref(false)
const availableTags = ref([])

// 获取内容详情
const fetchContentDetail = async () => {
  const contentId = route.query.id
  if (!contentId) {
    ElMessage.error('缺少内容ID')
    router.back()
    return
  }

  loading.value = true
  try {
    const response = await getContentDetail(contentId)
    const content = response

    form.id = content.id
    form.video_url = content.video_url
    form.cover_url = content.cover_url
    form.title = content.title
    form.description = content.description || ''
    form.content_type = content.content_type
    form.tag_ids = content.tags ? content.tags.map(tag => tag.id) : []
    form.status = content.status
    form.is_featured = Boolean(content.is_featured)  // 转换为布尔值
    form.priority = content.priority || 0
  } catch (error) {
    ElMessage.error('获取内容详情失败：' + (error.message || '未知错误'))
    router.back()
  } finally {
    loading.value = false
  }
}

// 获取标签列表
const fetchTags = async () => {
  try {
    const response = await getTagList({ page: 1, size: 100 })
    availableTags.value = response.tags || []
  } catch (error) {
    console.error('获取标签列表失败:', error)
  }
}

// 封面上传前检查
const beforeCoverUpload = (file) => {
  const isImage = ['image/jpeg', 'image/png'].includes(file.type)
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传 JPG、PNG 格式的图片')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }
  return true
}

// 封面上传成功
const handleCoverSuccess = (response) => {
  if (response.code === 0) {
    form.cover_url = response.data.url
    ElMessage.success('封面上传成功')
  } else {
    ElMessage.error('封面上传失败：' + response.message)
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    submitting.value = true

    const data = {
      cover_url: form.cover_url,
      title: form.title,
      description: form.description,
      content_type: form.content_type,
      tag_ids: form.tag_ids,
      is_featured: form.is_featured,
      priority: form.is_featured ? form.priority : 0
    }

    await updateContent(form.id, data)

    ElMessage.success('保存成功')
    router.push('/content')
  } catch (error) {
    if (error.message) {
      ElMessage.error('保存失败：' + error.message)
    }
  } finally {
    submitting.value = false
  }
}

// 删除内容
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除内容"${form.title}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    deleting.value = true
    await deleteContent(form.id)
    ElMessage.success('删除成功')
    router.push('/content')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + (error.message || '未知错误'))
    }
  } finally {
    deleting.value = false
  }
}

// 返回
const goBack = () => {
  router.back()
}

// 工具函数
const getStatusType = (status) => {
  const typeMap = {
    draft: 'info',
    under_review: 'warning',
    published: 'success',
    rejected: 'danger',
    removed: 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    draft: '草稿',
    under_review: '审核中',
    published: '已发布',
    rejected: '已驳回',
    removed: '已下架'
  }
  return textMap[status] || status
}

// 初始化
onMounted(() => {
  fetchTags()
  fetchContentDetail()
})
</script>

<style scoped>
.content-edit {
  padding: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.edit-card {
  margin-top: 20px;
  max-width: 800px;
}

.video-preview {
  border-radius: 8px;
  overflow: hidden;
}

.video-info {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.cover-uploader {
  display: inline-block;
}

.cover-image {
  width: 200px;
  height: 112px;
  object-fit: cover;
  border-radius: 8px;
  display: block;
  cursor: pointer;
}

.cover-placeholder {
  width: 200px;
  height: 112px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.cover-placeholder:hover {
  border-color: #409eff;
}

.cover-placeholder .el-icon {
  font-size: 28px;
  color: #c0c4cc;
  margin-bottom: 8px;
}

.cover-hint {
  font-size: 12px;
  color: #909399;
}

.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
