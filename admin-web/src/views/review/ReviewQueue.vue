<template>
  <div class="review-queue-container">
    <!-- 页面标题和统计 -->
    <el-card class="header-card" shadow="never">
      <div class="header-content">
        <div class="title-section">
          <h2>审核队列</h2>
          <p class="subtitle">管理待审核的内容</p>
        </div>
        <div class="stats-section">
          <el-statistic title="待审核" :value="statistics.pending_count || 0" />
          <el-statistic title="今日已审核" :value="statistics.today_reviewed || 0" />
          <el-statistic title="本周已审核" :value="statistics.week_reviewed || 0" />
        </div>
      </div>
    </el-card>

    <!-- 筛选和操作栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="内容类型">
          <el-select v-model="filterForm.content_type" placeholder="全部类型" clearable style="width: 150px">
            <el-option label="工作知识" value="工作知识" />
            <el-option label="生活分享" value="生活分享" />
            <el-option label="企业文化" value="企业文化" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="提交日期">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 批量操作 -->
      <div class="batch-actions" v-if="selectedContents.length > 0">
        <el-alert
          :title="`已选择 ${selectedContents.length} 项`"
          type="info"
          :closable="false"
        >
          <template #default>
            <el-button type="success" size="small" @click="handleBatchApprove">
              <el-icon><Check /></el-icon>
              批量批准
            </el-button>
            <el-button type="danger" size="small" @click="handleBatchReject">
              <el-icon><Close /></el-icon>
              批量拒绝
            </el-button>
          </template>
        </el-alert>
      </div>
    </el-card>

    <!-- 内容列表 -->
    <el-card class="content-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="contentList"
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
            />
          </template>
        </el-table-column>

        <el-table-column label="标题" min-width="200">
          <template #default="{ row }">
            <div class="content-title">
              <el-link type="primary" @click="handlePreview(row)">
                {{ row.title }}
              </el-link>
              <el-tag v-if="row.content_type" size="small" style="margin-left: 8px">
                {{ row.content_type }}
              </el-tag>
            </div>
            <div class="content-meta">
              <span>时长: {{ formatDuration(row.duration) }}</span>
              <span style="margin-left: 12px">大小: {{ formatFileSize(row.file_size) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="创作者" width="150">
          <template #default="{ row }">
            <div class="creator-info">
              <el-avatar :size="32" :src="row.creator?.avatar_url">
                {{ row.creator?.name?.charAt(0) }}
              </el-avatar>
              <div class="creator-details">
                <div>{{ row.creator?.name }}</div>
                <div class="creator-dept">{{ row.creator?.department }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="提交时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="AI审核" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.ai_analysis?.moderation_result?.is_safe === true" type="success" size="small">
              通过
            </el-tag>
            <el-tag v-else-if="row.ai_analysis?.moderation_result?.is_safe === false" type="danger" size="small">
              未通过
            </el-tag>
            <el-tag v-else type="info" size="small">
              待处理
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleViewDetail(row)">
              <el-icon><View /></el-icon>
              查看详情
            </el-button>
            <el-dropdown @command="(command) => handleAction(command, row)" style="margin-left: 8px">
              <el-button size="small">
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="approve">
                    <el-icon><Check /></el-icon>
                    批准
                  </el-dropdown-item>
                  <el-dropdown-item command="reject">
                    <el-icon><Close /></el-icon>
                    拒绝
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 内容预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="内容预览"
      width="80%"
      :close-on-click-modal="false"
    >
      <div v-if="currentContent" class="preview-content">
        <video
          v-if="currentContent.video_url"
          :src="currentContent.video_url"
          controls
          style="width: 100%; max-height: 500px"
        />
        <el-descriptions :column="2" border style="margin-top: 20px">
          <el-descriptions-item label="标题">{{ currentContent.title }}</el-descriptions-item>
          <el-descriptions-item label="内容类型">{{ currentContent.content_type }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ currentContent.description }}</el-descriptions-item>
          <el-descriptions-item label="创作者">{{ currentContent.creator?.name }}</el-descriptions-item>
          <el-descriptions-item label="部门">{{ currentContent.creator?.department }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ formatDateTime(currentContent.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="时长">{{ formatDuration(currentContent.duration) }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
        <el-button type="success" @click="handleApprove(currentContent)">
          <el-icon><Check /></el-icon>
          批准
        </el-button>
        <el-button type="danger" @click="handleReject(currentContent)">
          <el-icon><Close /></el-icon>
          拒绝
        </el-button>
      </template>
    </el-dialog>

    <!-- 拒绝原因对话框 -->
    <el-dialog
      v-model="rejectDialogVisible"
      title="拒绝内容"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="rejectForm" :rules="rejectRules" ref="rejectFormRef" label-width="80px">
        <el-form-item label="拒绝原因" prop="reason">
          <el-input
            v-model="rejectForm.reason"
            type="textarea"
            :rows="4"
            placeholder="请输入拒绝原因，将通知创作者"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmReject" :loading="submitting">
          确认拒绝
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Check,
  Close,
  View,
  ArrowDown
} from '@element-plus/icons-vue'
import {
  getReviewQueue,
  approveContent,
  rejectContent,
  batchReview,
  getReviewStatistics
} from '@/api/review'

// 数据
const loading = ref(false)
const contentList = ref([])
const selectedContents = ref([])
const statistics = ref({})

// 筛选表单
const filterForm = reactive({
  content_type: '',
  creator_id: ''
})
const dateRange = ref([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 预览对话框
const previewDialogVisible = ref(false)
const currentContent = ref(null)

// 拒绝对话框
const rejectDialogVisible = ref(false)
const rejectFormRef = ref(null)
const rejectForm = reactive({
  content_id: '',
  reason: ''
})
const rejectRules = {
  reason: [
    { required: true, message: '请输入拒绝原因', trigger: 'blur' },
    { min: 5, message: '拒绝原因至少5个字符', trigger: 'blur' }
  ]
}
const submitting = ref(false)
const rejectMode = ref('single') // 'single' or 'batch'

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...filterForm
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    const response = await getReviewQueue(params)
    contentList.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('加载审核队列失败:', error)
    ElMessage.error('加载审核队列失败')
  } finally {
    loading.value = false
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    statistics.value = await getReviewStatistics()
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadData()
}

// 重置
const handleReset = () => {
  filterForm.content_type = ''
  filterForm.creator_id = ''
  dateRange.value = []
  pagination.page = 1
  loadData()
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedContents.value = selection
}

// 分页变化
const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  loadData()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadData()
}

// 预览
const handlePreview = (content) => {
  currentContent.value = content
  previewDialogVisible.value = true
}

// 查看详情（跳转到详情页）
const handleViewDetail = (content) => {
  // TODO: 跳转到详情页
  handlePreview(content)
}

// 操作
const handleAction = (command, content) => {
  if (command === 'approve') {
    handleApprove(content)
  } else if (command === 'reject') {
    handleReject(content)
  }
}

// 批准
const handleApprove = async (content) => {
  try {
    await ElMessageBox.confirm(
      `确认批准内容"${content.title}"吗？`,
      '批准确认',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'success'
      }
    )
    
    loading.value = true
    await approveContent({
      content_id: content.id,
      comment: ''
    })
    
    ElMessage.success('批准成功')
    previewDialogVisible.value = false
    loadData()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批准失败:', error)
      ElMessage.error('批准失败')
    }
  } finally {
    loading.value = false
  }
}

// 拒绝
const handleReject = (content) => {
  rejectMode.value = 'single'
  rejectForm.content_id = content.id
  rejectForm.reason = ''
  rejectDialogVisible.value = true
}

// 确认拒绝
const confirmReject = async () => {
  if (!rejectFormRef.value) return
  
  await rejectFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (rejectMode.value === 'single') {
        await rejectContent({
          content_id: rejectForm.content_id,
          reason: rejectForm.reason
        })
        ElMessage.success('拒绝成功')
      } else {
        // 批量拒绝
        await batchReview({
          content_ids: selectedContents.value.map(c => c.id),
          action: 'reject',
          reason: rejectForm.reason
        })
        ElMessage.success('批量拒绝成功')
        selectedContents.value = []
      }
      
      rejectDialogVisible.value = false
      previewDialogVisible.value = false
      loadData()
      loadStatistics()
    } catch (error) {
      console.error('拒绝失败:', error)
      ElMessage.error('拒绝失败')
    } finally {
      submitting.value = false
    }
  })
}

// 批量批准
const handleBatchApprove = async () => {
  try {
    await ElMessageBox.confirm(
      `确认批准选中的 ${selectedContents.value.length} 项内容吗？`,
      '批量批准确认',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'success'
      }
    )
    
    loading.value = true
    await batchReview({
      content_ids: selectedContents.value.map(c => c.id),
      action: 'approve'
    })
    
    ElMessage.success('批量批准成功')
    selectedContents.value = []
    loadData()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量批准失败:', error)
      ElMessage.error('批量批准失败')
    }
  } finally {
    loading.value = false
  }
}

// 批量拒绝
const handleBatchReject = () => {
  rejectMode.value = 'batch'
  rejectForm.content_id = ''
  rejectForm.reason = ''
  rejectDialogVisible.value = true
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '-'
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 初始化
onMounted(() => {
  loadData()
  loadStatistics()
})
</script>

<style scoped>
.review-queue-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.stats-section {
  display: flex;
  gap: 40px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  margin-bottom: 0;
}

.batch-actions {
  margin-top: 16px;
}

.content-card {
  margin-bottom: 20px;
}

.content-title {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.content-meta {
  font-size: 12px;
  color: #909399;
}

.creator-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.creator-details {
  font-size: 12px;
}

.creator-dept {
  color: #909399;
  margin-top: 2px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.preview-content {
  max-height: 70vh;
  overflow-y: auto;
}
</style>
