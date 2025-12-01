<template>
  <div class="content-list">
    <!-- 页面标题和操作栏 -->
    <div class="header">
      <h2>内容管理</h2>
      <el-button type="primary" @click="goToUpload">
        <el-icon><Plus /></el-icon>
        上传内容
      </el-button>
    </div>

    <!-- 搜索和筛选区域 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索标题、描述或标签"
            clearable
            style="width: 300px"
            @clear="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="filterForm.status"
            placeholder="全部状态"
            clearable
            style="width: 150px"
            @change="handleSearch"
          >
            <el-option label="草稿" value="draft" />
            <el-option label="审核中" value="under_review" />
            <el-option label="已发布" value="published" />
            <el-option label="已驳回" value="rejected" />
            <el-option label="已下架" value="removed" />
          </el-select>
        </el-form-item>

        <el-form-item label="内容类型">
          <el-select
            v-model="filterForm.contentType"
            placeholder="全部类型"
            clearable
            style="width: 150px"
            @change="handleSearch"
          >
            <el-option label="工作知识" value="工作知识" />
            <el-option label="生活分享" value="生活分享" />
            <el-option label="企业文化" value="企业文化" />
          </el-select>
        </el-form-item>

        <el-form-item label="创作者">
          <el-input
            v-model="filterForm.creator"
            placeholder="创作者姓名"
            clearable
            style="width: 150px"
            @clear="handleSearch"
          />
        </el-form-item>

        <el-form-item label="精选">
          <el-select
            v-model="filterForm.featured"
            placeholder="全部"
            clearable
            style="width: 120px"
            @change="handleSearch"
          >
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 批量操作栏 -->
    <div class="batch-actions" v-if="selectedIds.length > 0">
      <span class="selected-info">已选择 {{ selectedIds.length }} 项</span>
      <el-button type="warning" @click="handleBatchRemove">批量下架</el-button>
      <el-button type="danger" @click="handleBatchDelete">批量删除</el-button>
      <el-button @click="handleClearSelection">取消选择</el-button>
    </div>

    <!-- 内容列表表格 -->
    <el-card class="table-card">
      <el-table
        :data="contentList"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column label="封面" width="120">
          <template #default="{ row }">
            <el-image
              :src="row.cover_url || '/placeholder.png'"
              fit="cover"
              style="width: 100px; height: 60px; border-radius: 4px"
              :preview-src-list="[row.cover_url]"
              :preview-teleported="true"
              :z-index="9999"
            />
          </template>
        </el-table-column>

        <el-table-column label="标题" prop="title" min-width="200" show-overflow-tooltip />

        <el-table-column label="创作者" width="120">
          <template #default="{ row }">
            <div>{{ row.creator?.name || '-' }}</div>
            <div class="text-secondary">{{ row.creator?.department || '-' }}</div>
          </template>
        </el-table-column>

        <el-table-column label="内容类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.content_type || '-' }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="统计" width="220">
          <template #default="{ row }">
            <div class="stats">
              <span>观看: {{ row.view_count || 0 }}</span>
              <span>点赞: {{ row.like_count || 0 }}</span>
              <span>收藏: {{ row.favorite_count || 0 }}</span>
              <span>评论: {{ row.comment_count || 0 }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="精选" width="80" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.is_featured" color="#f59e0b" :size="20">
              <Star />
            </el-icon>
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleViewDetail(row)">
              查看
            </el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button 
              v-if="row.status === 'removed'" 
              link 
              type="success" 
              size="small" 
              @click="handleRestore(row)"
            >
              恢复
            </el-button>
            <el-button 
              v-else-if="row.status === 'published'" 
              link 
              type="warning" 
              size="small" 
              @click="handleRemove(row)"
            >
              下架
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 内容详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="内容详情"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="currentContent" class="content-detail">
        <!-- 视频预览 -->
        <div class="video-preview">
          <video
            v-if="currentContent.video_url"
            :src="currentContent.video_url"
            controls
            style="width: 100%; max-height: 400px"
          />
        </div>

        <!-- 基本信息 -->
        <el-descriptions :column="2" border class="detail-section">
          <el-descriptions-item label="标题">
            {{ currentContent.title }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentContent.status)">
              {{ getStatusText(currentContent.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="内容类型">
            {{ currentContent.content_type || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="时长">
            {{ formatDuration(currentContent.duration) }}
          </el-descriptions-item>
          <el-descriptions-item label="创作者">
            {{ currentContent.creator?.name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="部门">
            {{ currentContent.creator?.department || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDate(currentContent.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentContent.description || '-' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 标签 -->
        <div class="detail-section">
          <h4>标签</h4>
          <div class="tags">
            <el-tag
              v-for="tag in currentContent.tags"
              :key="tag.id"
              class="tag-item"
              size="small"
            >
              {{ tag.name }}
            </el-tag>
            <span v-if="!currentContent.tags || currentContent.tags.length === 0">
              暂无标签
            </span>
          </div>
        </div>

        <!-- 统计数据 -->
        <div class="detail-section">
          <h4>统计数据</h4>
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ currentContent.view_count || 0 }}</div>
                <div class="stat-label">观看次数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ currentContent.like_count || 0 }}</div>
                <div class="stat-label">点赞数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ currentContent.favorite_count || 0 }}</div>
                <div class="stat-label">收藏数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-item clickable" @click="loadComments">
                <div class="stat-value">{{ currentContent.comment_count || 0 }}</div>
                <div class="stat-label">评论数 <el-icon><View /></el-icon></div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 评论列表 -->
        <div class="detail-section" v-if="showComments">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <h4 style="margin: 0;">评论列表</h4>
            <el-button size="small" @click="showComments = false">收起</el-button>
          </div>
          <div v-loading="commentsLoading">
            <div v-if="comments.length === 0" style="text-align: center; color: #909399; padding: 20px;">
              暂无评论
            </div>
            <div v-else class="comments-list">
              <div v-for="comment in comments" :key="comment.id" class="comment-item">
                <div class="comment-header">
                  <div class="comment-user">
                    <el-avatar :size="32" :src="comment.user?.avatar_url">
                      {{ comment.user?.name?.charAt(0) || '?' }}
                    </el-avatar>
                    <div class="comment-user-info">
                      <div class="comment-user-name">{{ comment.user?.name || '未知用户' }}</div>
                      <div class="comment-time">{{ formatDate(comment.created_at) }}</div>
                    </div>
                  </div>
                </div>
                <div class="comment-content">{{ comment.text }}</div>
                <div class="comment-footer" v-if="comment.reply_count > 0">
                  <span class="comment-replies">
                    {{ comment.reply_count }} 条回复
                  </span>
                </div>
              </div>
            </div>
            <div v-if="commentsPagination.total > commentsPagination.size" class="comments-pagination">
              <el-pagination
                v-model:current-page="commentsPagination.page"
                :page-size="commentsPagination.size"
                :total="commentsPagination.total"
                layout="prev, pager, next"
                small
                @current-change="loadComments"
              />
            </div>
          </div>
        </div>

        <!-- AI分析结果 -->
        <div class="detail-section" v-if="currentContent.ai_analysis">
          <h4>AI分析结果</h4>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="场景描述">
              {{ currentContent.ai_analysis.scene_description || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="语音转录">
              {{ currentContent.ai_analysis.transcript || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="OCR文字">
              {{ currentContent.ai_analysis.ocr_text || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="审核结果">
              <el-tag :type="currentContent.ai_analysis.moderation_result?.is_safe ? 'success' : 'danger'">
                {{ currentContent.ai_analysis.moderation_result?.is_safe ? '安全' : '需要审核' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleEdit(currentContent)">编辑</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Star, View } from '@element-plus/icons-vue'
import {
  getContentList,
  getContentDetail,
  deleteContent,
  batchDeleteContent,
  getContentComments,
  removeContent,
  batchRemoveContent,
  restoreContent
} from '../../api/content'

const router = useRouter()

// 数据状态
const loading = ref(false)
const contentList = ref([])
const selectedIds = ref([])
const detailDialogVisible = ref(false)
const currentContent = ref(null)
const showComments = ref(false)
const commentsLoading = ref(false)
const comments = ref([])
const commentsPagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

// 筛选表单
const filterForm = reactive({
  keyword: '',
  status: '',
  contentType: '',
  creator: '',
  featured: null
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 获取内容列表
const fetchContentList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...filterForm
    }
    
    const response = await getContentList(params)
    contentList.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    ElMessage.error('获取内容列表失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchContentList()
}

// 重置筛选
const handleReset = () => {
  filterForm.keyword = ''
  filterForm.status = ''
  filterForm.contentType = ''
  filterForm.creator = ''
  filterForm.featured = null
  handleSearch()
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedIds.value = selection.map(item => item.id)
}

// 清除选择
const handleClearSelection = () => {
  selectedIds.value = []
}

// 批量下架
const handleBatchRemove = async () => {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      `确定要下架选中的 ${selectedIds.value.length} 项内容吗？请输入下架原因：`,
      '批量下架确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /.+/,
        inputErrorMessage: '请输入下架原因',
        inputPlaceholder: '例如：违反社区规范'
      }
    )

    await batchRemoveContent(selectedIds.value, reason)
    ElMessage.success('批量下架成功')
    selectedIds.value = []
    fetchContentList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量下架失败：' + (error.message || '未知错误'))
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 项内容吗？此操作不可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await batchDeleteContent(selectedIds.value)
    ElMessage.success('批量删除成功')
    selectedIds.value = []
    fetchContentList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败：' + (error.message || '未知错误'))
    }
  }
}

// 查看详情
const handleViewDetail = async (row) => {
  try {
    const response = await getContentDetail(row.id)
    currentContent.value = response
    showComments.value = false
    comments.value = []
    commentsPagination.page = 1
    commentsPagination.total = 0
    detailDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取内容详情失败：' + (error.message || '未知错误'))
  }
}

// 加载评论列表
const loadComments = async () => {
  if (!currentContent.value) return
  
  showComments.value = true
  commentsLoading.value = true
  
  try {
    const response = await getContentComments(currentContent.value.id, {
      page: commentsPagination.page,
      page_size: commentsPagination.size
    })
    
    comments.value = response.comments || []
    commentsPagination.total = response.total || 0
  } catch (error) {
    ElMessage.error('获取评论列表失败：' + (error.message || '未知错误'))
  } finally {
    commentsLoading.value = false
  }
}

// 编辑
const handleEdit = (row) => {
  router.push({
    path: '/content/edit',
    query: { id: row.id }
  })
}

// 下架
const handleRemove = async (row) => {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      `确定要下架内容"${row.title}"吗？请输入下架原因：`,
      '下架确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /.+/,
        inputErrorMessage: '请输入下架原因',
        inputPlaceholder: '例如：违反社区规范'
      }
    )

    await removeContent(row.id, reason)
    ElMessage.success('下架成功')
    fetchContentList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('下架失败：' + (error.message || '未知错误'))
    }
  }
}

// 恢复
const handleRestore = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要恢复内容"${row.title}"吗？`,
      '恢复确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    await restoreContent(row.id)
    ElMessage.success('恢复成功')
    fetchContentList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('恢复失败：' + (error.message || '未知错误'))
    }
  }
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除内容"${row.title}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteContent(row.id)
    ElMessage.success('删除成功')
    fetchContentList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + (error.message || '未知错误'))
    }
  }
}

// 跳转到上传页面
const goToUpload = () => {
  router.push('/content/upload')
}

// 分页变化
const handleSizeChange = () => {
  pagination.page = 1
  fetchContentList()
}

const handlePageChange = () => {
  fetchContentList()
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

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDuration = (seconds) => {
  if (!seconds) return '-'
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

// 初始化
onMounted(() => {
  fetchContentList()
})
</script>

<style scoped>
.content-list {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  margin-bottom: 0;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 20px;
}

.selected-info {
  color: #606266;
  font-size: 14px;
}

.table-card {
  margin-bottom: 20px;
}

.text-secondary {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.content-detail {
  max-height: 70vh;
  overflow-y: auto;
  overflow-x: hidden;
}

.content-detail .el-descriptions,
.content-detail .el-row,
.content-detail .detail-section {
  max-width: 100%;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
}

.video-preview {
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  max-width: 100%;
}

.video-preview video {
  max-width: 100%;
  height: auto;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  margin: 0;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.stat-item.clickable {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-item.clickable:hover {
  background-color: #ecf5ff;
  transform: translateY(-2px);
}

.stat-item.clickable .stat-label {
  color: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.comments-list {
  max-height: 400px;
  overflow-y: auto;
}

.comment-item {
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comment-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.comment-user-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.comment-user-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.comment-time {
  font-size: 12px;
  color: #909399;
}

.comment-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 8px;
  padding-left: 44px;
}

.comment-footer {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-left: 44px;
  font-size: 12px;
  color: #909399;
}

.comment-likes,
.comment-replies {
  display: flex;
  align-items: center;
  gap: 4px;
}

.comments-pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}
</style>
