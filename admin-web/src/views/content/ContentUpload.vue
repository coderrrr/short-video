<template>
  <div class="content-upload">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="page-title">上传内容</span>
      </template>
    </el-page-header>

    <el-card class="upload-card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        label-position="right"
      >
        <!-- 视频上传 -->
        <el-form-item label="视频文件" required>
          <el-upload
            ref="uploadRef"
            class="video-uploader"
            :action="uploadAction"
            :headers="uploadHeaders"
            :on-success="handleVideoSuccess"
            :on-error="handleVideoError"
            :on-progress="handleVideoProgress"
            :before-upload="beforeVideoUpload"
            :show-file-list="false"
            accept="video/mp4,video/quicktime,video/x-msvideo,.mp4,.mov,.avi"
            drag
          >
            <div v-if="!form.video_url" class="upload-placeholder">
              <el-icon class="upload-icon"><Upload /></el-icon>
              <div class="upload-text">
                <p>点击或拖拽视频文件到此处上传</p>
                <p class="upload-hint">支持 MP4、MOV、AVI 格式，文件大小不超过 500MB</p>
              </div>
            </div>
            <div v-else class="video-preview">
              <video :src="form.video_url" controls style="width: 100%; max-height: 300px" />
              <el-button class="reupload-btn" type="primary" size="small">
                重新上传
              </el-button>
            </div>
          </el-upload>
          <el-progress
            v-if="uploadProgress > 0 && uploadProgress < 100"
            :percentage="uploadProgress"
            :stroke-width="8"
            class="upload-progress"
          />
        </el-form-item>

        <!-- 封面图片 -->
        <el-form-item label="封面图片" prop="cover_url">
          <el-upload
            class="cover-uploader"
            :action="coverUploadAction"
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

        <!-- 自动发布 -->
        <el-form-item label="发布设置">
          <el-checkbox v-model="form.auto_publish">
            自动发布（跳过审核流程）
          </el-checkbox>
          <div class="form-hint">管理员上传的内容可以选择自动发布</div>
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
            {{ form.auto_publish ? '发布' : '提交审核' }}
          </el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 批量上传对话框 -->
    <el-dialog
      v-model="batchUploadVisible"
      title="批量上传"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-upload
        ref="batchUploadRef"
        class="batch-upload"
        :action="uploadAction"
        :headers="uploadHeaders"
        :on-success="handleBatchSuccess"
        :on-error="handleBatchError"
        :file-list="batchFileList"
        accept="video/mp4,video/quicktime,video/x-msvideo,.mp4,.mov,.avi"
        multiple
        drag
      >
        <el-icon class="upload-icon"><Upload /></el-icon>
        <div class="upload-text">
          <p>点击或拖拽多个视频文件到此处</p>
          <p class="upload-hint">支持批量上传，每个文件不超过 500MB</p>
        </div>
      </el-upload>

      <template #footer>
        <el-button @click="batchUploadVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Upload, Plus } from '@element-plus/icons-vue'
import { uploadContent } from '../../api/content'
import { getTagList } from '../../api/tag'

const router = useRouter()

// 表单引用
const formRef = ref(null)
const uploadRef = ref(null)
const batchUploadRef = ref(null)

// 上传配置 - 只用于上传文件，不创建内容记录
const uploadAction = import.meta.env.VITE_API_BASE_URL + '/admin/upload/video'
const coverUploadAction = import.meta.env.VITE_API_BASE_URL + '/admin/upload/image'
const uploadHeaders = computed(() => ({
  Authorization: 'Bearer ' + localStorage.getItem('admin_token')
}))

// 表单数据
const form = reactive({
  video_url: '',
  cover_url: '',
  title: '',
  description: '',
  content_type: '',
  tag_ids: [],
  auto_publish: true,
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
const uploadProgress = ref(0)
const submitting = ref(false)
const availableTags = ref([])
const batchUploadVisible = ref(false)
const batchFileList = ref([])

// 获取标签列表
const fetchTags = async () => {
  try {
    const response = await getTagList({ page: 1, size: 100 })
    availableTags.value = response.tags || []
  } catch (error) {
    console.error('获取标签列表失败:', error)
  }
}

// 视频上传前检查
const beforeVideoUpload = (file) => {
  const isVideo = ['video/mp4', 'video/quicktime', 'video/x-msvideo'].includes(file.type)
  const isLt500M = file.size / 1024 / 1024 < 500

  if (!isVideo) {
    ElMessage.error('只能上传 MP4、MOV、AVI 格式的视频文件')
    return false
  }
  if (!isLt500M) {
    ElMessage.error('视频文件大小不能超过 500MB')
    return false
  }
  return true
}

// 视频上传进度
const handleVideoProgress = (event) => {
  uploadProgress.value = Math.floor(event.percent)
}

// 视频上传成功
const handleVideoSuccess = (response) => {
  // 后端直接返回 { url, filename, size, content_type }
  if (response.url) {
    // 如果是相对路径，添加服务器地址
    if (response.url.startsWith('http')) {
      form.video_url = response.url
    } else {
      // 从 VITE_API_BASE_URL 中提取服务器地址
      const baseUrl = import.meta.env.VITE_API_BASE_URL
      form.video_url = baseUrl + response.url
    }
    ElMessage.success('视频上传成功')
    uploadProgress.value = 0
  } else {
    ElMessage.error('视频上传失败：响应格式错误')
  }
}

// 视频上传失败
const handleVideoError = (error) => {
  console.error('视频上传失败:', error)
  let errorMsg = '视频上传失败'
  try {
    const errorData = JSON.parse(error.message)
    errorMsg = errorData.detail || errorMsg
  } catch (e) {
    errorMsg = error.message || errorMsg
  }
  ElMessage.error(errorMsg)
  uploadProgress.value = 0
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
  // 后端直接返回 { url, filename, size, content_type }
  if (response.url) {
    // 如果是相对路径，添加服务器地址
    if (response.url.startsWith('http')) {
      form.cover_url = response.url
    } else {
      // 从 VITE_API_BASE_URL 中提取服务器地址
      const baseUrl = import.meta.env.VITE_API_BASE_URL
      form.cover_url = baseUrl + response.url
    }
    ElMessage.success('封面上传成功')
  } else {
    ElMessage.error('封面上传失败：响应格式错误')
  }
}

// 批量上传成功
const handleBatchSuccess = (response, file) => {
  if (response.url) {
    ElMessage.success(`${file.name} 上传成功`)
  } else {
    ElMessage.error(`${file.name} 上传失败：响应格式错误`)
  }
}

// 批量上传失败
const handleBatchError = (error, file) => {
  ElMessage.error(`${file.name} 上传失败：${error.message}`)
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    if (!form.video_url) {
      ElMessage.error('请先上传视频文件')
      return
    }

    submitting.value = true

    const data = {
      video_url: form.video_url,
      cover_url: form.cover_url,
      title: form.title,
      description: form.description,
      content_type: form.content_type,
      tag_ids: form.tag_ids,
      auto_publish: form.auto_publish,
      is_featured: form.is_featured,
      priority: form.is_featured ? form.priority : 0
    }

    await uploadContent(data)
    ElMessage.success(form.auto_publish ? '内容发布成功' : '内容提交成功')
    router.push('/content')
  } catch (error) {
    if (error.message) {
      ElMessage.error('提交失败：' + error.message)
    }
  } finally {
    submitting.value = false
  }
}

// 返回
const goBack = () => {
  router.back()
}

// 初始化
onMounted(() => {
  fetchTags()
})
</script>

<style scoped>
.content-upload {
  padding: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.upload-card {
  margin-top: 20px;
  max-width: 800px;
}

.video-uploader {
  width: 100%;
}

.upload-placeholder {
  padding: 60px 20px;
  text-align: center;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-placeholder:hover {
  border-color: #409eff;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-text p {
  margin: 8px 0;
  color: #606266;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
}

.video-preview {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
}

.reupload-btn {
  position: absolute;
  top: 10px;
  right: 10px;
}

.upload-progress {
  margin-top: 10px;
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

.batch-upload {
  width: 100%;
}
</style>
